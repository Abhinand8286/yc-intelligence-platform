import asyncio
import hashlib
import json
import time
import logging
import psycopg2
from playwright.async_api import async_playwright
from datetime import datetime

# === CONFIGURATION ===
YC_URL = "https://www.ycombinator.com/companies" 
DB_CONFIG = "postgresql://postgres:12341@localhost:5432/postgres"
LOG_FILE = "scraper_ultimate.log"

# === SETUP LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def get_db_connection():
    return psycopg2.connect(DB_CONFIG)

def calculate_hash(data_dict):
    data_str = json.dumps(data_dict, sort_keys=True)
    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

async def scrape_with_playwright():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Start Scrape Run Log
        cursor.execute("INSERT INTO scrape_runs (started_at, status) VALUES (NOW(), 'running') RETURNING id")
        run_id = cursor.fetchone()[0]
        conn.commit()
    except Exception as e:
        print(f"Database Connection Failed immediately: {e}")
        return

    stats = {'found': 0, 'added': 0, 'updated': 0, 'failed': 0}
    logging.info(f"--- Starting Ultimate Scrape Run #{run_id} ---")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        logging.info(f"Navigating to {YC_URL}...")
        try:
            await page.goto(YC_URL, timeout=60000)
            
            # === INFINITE SCROLL ===
            logging.info("Starting Infinite Scroll...")
            last_height = await page.evaluate("document.body.scrollHeight")
            
            while True:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000) 
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    logging.info("Reached bottom of page.")
                    break
                last_height = new_height
                logging.info("Scrolled deeper...")

            # === EXTRACT DATA ===
            company_elements = await page.query_selector_all('a[href*="/companies/"]') 
            logging.info(f"Found {len(company_elements)} company elements. Processing...")

            for el in company_elements:
                stats['found'] += 1
                try:
                    # Extract Data
                    raw_text = await el.inner_text()
                    href = await el.get_attribute('href')
                    full_url = f"https://www.ycombinator.com{href}"
                    
                    lines = raw_text.split('\n')
                    name = lines[0] if lines else "Unknown"
                    location = lines[1] if len(lines) > 1 else "Unknown"
                    description = lines[2] if len(lines) > 2 else ""
                    
                    # --- DATABASE OPERATIONS ---
                    cursor.execute("""
                        INSERT INTO companies (name, domain, is_active) 
                        VALUES (%s, %s, true) 
                        ON CONFLICT (name) DO UPDATE SET last_seen_at = NOW(), is_active = true 
                        RETURNING id
                    """, (name, full_url))
                    
                    if cursor.rowcount == 0:
                        cursor.execute("SELECT id FROM companies WHERE name = %s", (name,))
                    company_id = cursor.fetchone()[0]

                    # Hash Check
                    snapshot_data = {"desc": description, "loc": location}
                    new_hash = calculate_hash(snapshot_data)

                    cursor.execute("SELECT data_hash FROM company_snapshots WHERE company_id = %s ORDER BY scraped_at DESC LIMIT 1", (company_id,))
                    last_snap = cursor.fetchone()

                    if not last_snap or last_snap[0] != new_hash:
                        cursor.execute("""
                            INSERT INTO company_snapshots 
                            (company_id, location, description, scraped_at, data_hash)
                            VALUES (%s, %s, %s, NOW(), %s)
                        """, (company_id, location, description, new_hash))
                        
                        if last_snap:
                            stats['updated'] += 1
                        else:
                            stats['added'] += 1
                    
                    conn.commit() # Save this specific company

                except Exception as e:
                    # FIX: ROLLBACK IF ONE COMPANY FAILS
                    conn.rollback() 
                    stats['failed'] += 1
                    # logging.warning(f"Skipped {name}: {e}")

            # Update Run Log on Success
            cursor.execute("""
                UPDATE scrape_runs SET completed_at = NOW(), status = 'success', 
                companies_found = %s, companies_added = %s, companies_updated = %s, companies_failed = %s
                WHERE id = %s
            """, (stats['found'], stats['added'], stats['updated'], stats['failed'], run_id))
            conn.commit()

        except Exception as e:
            # FIX: ROLLBACK BEFORE LOGGING FAILURE
            conn.rollback() 
            logging.error(f"Critical Scraper Error: {e}")
            try:
                cursor.execute("UPDATE scrape_runs SET status = 'failed' WHERE id = %s", (run_id,))
                conn.commit()
            except:
                pass # If even logging fails, just give up
        
        finally:
            await browser.close()
            cursor.close()
            conn.close()

if __name__ == "__main__":
    asyncio.run(scrape_with_playwright())
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
LOG_FILE = "scraper_production.log"

# === SETUP LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

def get_db_connection():
    return psycopg2.connect(DB_CONFIG)

def calculate_hash(data_dict):
    data_str = json.dumps(data_dict, sort_keys=True)
    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

async def scrape_with_playwright():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Start Run
    run_start_time = datetime.now()
    cursor.execute("INSERT INTO scrape_runs (started_at, status) VALUES (NOW(), 'running') RETURNING id")
    run_id = cursor.fetchone()[0]
    conn.commit()

    stats = {'found': 0, 'added': 0, 'updated': 0, 'failed': 0, 'total_time_ms': 0}
    logging.info(f"--- Starting Production Run #{run_id} ---")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # === TIMING: INDEX FETCH ===
            t0 = time.time()
            await page.goto(YC_URL, timeout=60000)
            index_fetch_time = (time.time() - t0) * 1000
            logging.info(f"Index fetch took {index_fetch_time:.2f}ms")

            # === INFINITE SCROLL ===
            logging.info("Starting Infinite Scroll...")
            last_height = await page.evaluate("document.body.scrollHeight")
            while True:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000) 
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == last_height: break
                last_height = new_height
            
            # === PARSING ===
            t_parse_start = time.time()
            company_elements = await page.query_selector_all('a[href*="/companies/"]') 
            parsing_time = (time.time() - t_parse_start) * 1000
            logging.info(f"HTML Parsing took {parsing_time:.2f}ms")

            for el in company_elements:
                stats['found'] += 1
                comp_start = time.time()
                
                try:
                    # Extract Data
                    raw_text = await el.inner_text()
                    href = await el.get_attribute('href')
                    full_url = f"https://www.ycombinator.com{href}"
                    
                    lines = raw_text.split('\n')
                    name = lines[0] if lines else "Unknown"
                    location = lines[1] if len(lines) > 1 else "Unknown"
                    description = lines[2] if len(lines) > 2 else ""

                    # === TIMING: DB WRITE ===
                    t_db_start = time.time()
                    
                    # 1. Update Companies Table (Set last_seen_at)
                    cursor.execute("""
                        INSERT INTO companies (name, domain, is_active, first_seen_at, last_seen_at) 
                        VALUES (%s, %s, true, NOW(), NOW()) 
                        ON CONFLICT (name) DO UPDATE 
                        SET last_seen_at = NOW(), is_active = true 
                        RETURNING id
                    """, (name, full_url))
                    
                    if cursor.rowcount == 0:
                        cursor.execute("SELECT id FROM companies WHERE name = %s", (name,))
                    company_id = cursor.fetchone()[0]

                    # 2. Check Hash & Snapshot
                    snapshot_data = {"desc": description, "loc": location}
                    new_hash = calculate_hash(snapshot_data)
                    cursor.execute("SELECT data_hash FROM company_snapshots WHERE company_id = %s ORDER BY scraped_at DESC LIMIT 1", (company_id,))
                    last_snap = cursor.fetchone()

                    if not last_snap or last_snap[0] != new_hash:
                        cursor.execute("""
                            INSERT INTO company_snapshots (company_id, location, description, scraped_at, data_hash)
                            VALUES (%s, %s, %s, NOW(), %s)
                        """, (company_id, location, description, new_hash))
                        if last_snap: stats['updated'] += 1
                        else: stats['added'] += 1
                    
                    conn.commit()
                    
                    # Calculate per-company time
                    comp_time_ms = (time.time() - comp_start) * 1000
                    stats['total_time_ms'] += comp_time_ms

                except Exception as e:
                    conn.rollback()
                    stats['failed'] += 1

            # === CLEANUP: MARK INACTIVE ===
            # If a company wasn't seen in this run (last_seen_at < run_start_time), mark is_active = false
            logging.info("Marking missing companies as inactive...")
            cursor.execute("""
                UPDATE companies SET is_active = false 
                WHERE last_seen_at < %s
            """, (run_start_time,))
            conn.commit()

            # Finish Log
            avg_time = stats['total_time_ms'] / stats['found'] if stats['found'] > 0 else 0
            cursor.execute("""
                UPDATE scrape_runs SET completed_at = NOW(), status = 'success', 
                companies_found = %s, companies_added = %s, companies_updated = %s, 
                companies_failed = %s, avg_time_per_company_ms = %s
                WHERE id = %s
            """, (stats['found'], stats['added'], stats['updated'], stats['failed'], avg_time, run_id))
            conn.commit()

        except Exception as e:
            conn.rollback()
            logging.error(f"Critical Error: {e}")
            cursor.execute("UPDATE scrape_runs SET status = 'failed' WHERE id = %s", (run_id,))
            conn.commit()
        
        finally:
            await browser.close()
            cursor.close()
            conn.close()

if __name__ == "__main__":
    asyncio.run(scrape_with_playwright())
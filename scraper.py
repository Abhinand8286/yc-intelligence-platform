import asyncio
import aiohttp
import logging
import json
import time
from datetime import datetime
from db_logic import get_db_pool, process_company_record

# === CONFIGURATION ===
# API Key 
API_KEY = "MjBjYjRiMzY0NzdhZWY0NjExY2NhZjYxMGIxYjc2MTAwNWFkNTkwNTc4NjgxYjU0YzFhYTY2ZGQ5OGY5NDMxZnJlc3RyaWN0SW5kaWNlcz0lNUIlMjJZQ0NvbXBhbnlfcHJvZHVjdGlvbiUyMiUyQyUyMllDQ29tcGFueV9CeV9MYXVuY2hfRGF0ZV9wcm9kdWN0aW9uJTIyJTVEJnRhZ0ZpbHRlcnM9JTVCJTIyeWNkY19wdWJsaWMlMjIlNUQmYW5hbHl0aWNzVGFncz0lNUIlMjJ5Y2RjJTIyJTVE"
APP_ID = "45BWZJ1SGC"
ALGOLIA_URL = f"https://{APP_ID}-dsn.algolia.net/1/indexes/*/queries"

# === LOGGING SETUP (Requirement: Save to scraper.log) ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log", mode='w'), # Save to file
        logging.StreamHandler()             # Show in console
    ],
    force=True
)

class YcScraper:
    def __init__(self, db_url):
        self.db_url = db_url
        self.pool = None
        # Stats tracking for scrape_runs table
        self.stats = {
            "total": 0, "new": 0, "updated": 0, "unchanged": 0, "failed": 0,
            "total_time_ms": 0, "slowest_ms": 0
        }

    async def fetch_batch(self, session, page):
        t_start = time.time()
        headers = { "x-algolia-api-key": API_KEY, "x-algolia-application-id": APP_ID }
        payload = {
            "requests": [{
                "indexName": "YCCompany_production",
                "params": f"hitsPerPage=100&page={page}"
            }]
        }
        try:
            async with session.post(ALGOLIA_URL, json=payload, headers=headers) as resp:
                fetch_time = (time.time() - t_start) * 1000
                if resp.status == 200:
                    return await resp.json(), fetch_time
                logging.error(f"API failed: {resp.status}")
                return None, fetch_time
        except Exception as e:
            logging.error(f"Net error: {e}")
            return None, 0

    async def run_cleanup(self, start_time):
        """Requirement: If a company disappears, mark is_active = false"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE companies 
                SET is_active = FALSE 
                WHERE last_seen_at < $1
            """, start_time)
            logging.info(f"Cleanup: Marked {result} companies as inactive.")

    async def save_run_stats(self, start_dt, end_dt):
        """Requirement: Track each scraper execution in scrape_runs"""
        avg_time = self.stats['total_time_ms'] / self.stats['total'] if self.stats['total'] > 0 else 0
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO scrape_runs 
                (started_at, ended_at, total_companies, new_companies, updated_companies, 
                unchanged_companies, failed_companies, avg_time_per_company_ms)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, start_dt, end_dt, self.stats['total'], self.stats['new'], 
            self.stats['updated'], self.stats['unchanged'], self.stats['failed'], avg_time)

    async def scrape(self):
        self.pool = await get_db_pool(self.db_url)
        start_dt = datetime.now()
        logging.info("Starting production scrape run...")
        
        async with aiohttp.ClientSession() as session:
            page = 0
            while True:
                # 1. Performance: Measure Fetch Time
                data, fetch_ms = await self.fetch_batch(session, page)
                
                if not data or 'results' not in data: break
                hits = data['results'][0]['hits']
                if not hits: break
                
                tasks = []
                for company in hits:
                    # 2. Performance: Tracking per company
                    company_start = time.time()
                    
                    clean_data = {
                        'yc_company_id': company.get('slug') or str(company.get('objectID')),
                        'name': company.get('name'),
                        'domain': company.get('website'),
                        'batch': company.get('batch'),
                        'stage': company.get('status'),
                        'description': company.get('one_liner'),
                        'location': company.get('location'),
                        'tags': company.get('tags', []),
                        'employee_range': str(company.get('team_size')) if company.get('team_size') else None
                    }
                    
                    # 3. DB Write Time is handled inside process_company_record, 
                    # but we track total end-to-end time here.
                    tasks.append(process_company_record(self.pool, clean_data))

                # Wait for DB writes
                results = await asyncio.gather(*tasks)
                
                # Update Stats
                for res in results:
                    self.stats['total'] += 1
                    if res == "new": self.stats['new'] += 1
                    elif res == "updated": self.stats['updated'] += 1
                    elif res == "unchanged": self.stats['unchanged'] += 1
                
                # Log performance for this batch
                logging.info(f"Page {page}: Fetched in {fetch_ms:.2f}ms. Processed {len(hits)} companies.")
                
                page += 1
                await asyncio.sleep(0.2)

        # === FINAL REQUIREMENTS ===
        end_dt = datetime.now()
        
        # 1. Run Cleanup (Mark Inactive)
        await self.run_cleanup(start_dt)
        
        # 2. Save Stats to DB
        await self.save_run_stats(start_dt, end_dt)
        
        # 3. Print Final Summary (As requested)
        print("\n=== FINAL PERFORMANCE REPORT ===")
        print(f"Total Companies: {self.stats['total']}")
        print(f"New: {self.stats['new']} | Updated: {self.stats['updated']}")
        print(f"Total Runtime: {end_dt - start_dt}")
        print("Detailed logs saved to scraper.log")
        print("================================")

        await self.pool.close()

if __name__ == "__main__":
    DB_URL = "postgresql://postgres:12341@localhost:5432/postgres"
    asyncio.run(YcScraper(DB_URL).scrape())
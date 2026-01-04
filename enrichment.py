import asyncio
import aiohttp
import re
import logging
from db_logic import get_db_pool

# setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# simple regex to find emails
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

class Enricher:
    def __init__(self, db_url):
        self.db_url = db_url
        self.pool = None

    async def check_site(self, session, company_id, url):
        if not url: return None
        
        # fix url if missing http
        if not url.startswith('http'): url = 'http://' + url

        try:
            # strict 3s timeout rule
            timeout = aiohttp.ClientTimeout(total=3)
            async with session.get(url, timeout=timeout, ssl=False) as resp:
                text = await resp.text()
                
                # find email
                emails = re.findall(EMAIL_REGEX, text)
                email = emails[0] if emails else None
                
                # check keywords
                has_careers = 'career' in text.lower() or 'jobs' in text.lower()
                has_blog = 'blog' in text.lower()
                
                return (company_id, has_careers, has_blog, email)

        except Exception:
            # if site is dead, just move on
            return None

    async def save_results(self, results):
        if not results: return
        
        async with self.pool.acquire() as conn:
            # bulk insert is faster
            await conn.executemany("""
                INSERT INTO company_web_enrichment 
                (company_id, has_careers_page, has_blog, contact_email, scraped_at)
                VALUES ($1, $2, $3, $4, NOW())
            """, results)

    async def run(self):
        self.pool = await get_db_pool(self.db_url)
        
        # get all companies that need checking
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, domain FROM companies WHERE domain IS NOT NULL")
            logging.info(f"found {len(rows)} companies to scan...")

        async with aiohttp.ClientSession() as session:
            # process in chunks of 50 so we don't crash the internet
            chunk_size = 50
            for i in range(0, len(rows), chunk_size):
                chunk = rows[i:i+chunk_size]
                tasks = []
                
                for row in chunk:
                    tasks.append(self.check_site(session, row['id'], row['domain']))
                
                # run batch
                results = await asyncio.gather(*tasks)
                
                # filter out failed sites (nones)
                valid_results = [r for r in results if r is not None]
                
                # save to db
                await self.save_results(valid_results)
                logging.info(f"processed {i + len(chunk)} / {len(rows)}")

        await self.pool.close()
        logging.info("enrichment complete.")

if __name__ == "__main__":
    # match your db url
    DB_URL = "postgresql://postgres:12341@localhost:5432/postgres"
    asyncio.run(Enricher(DB_URL).run())
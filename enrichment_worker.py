import psycopg2
import requests
import re
import logging
from urllib.parse import urlparse

# === CONFIGURATION ===
DB_CONFIG = "postgresql://postgres:12341@localhost:5432/postgres"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_enrichment_data(url):
    data = {'has_careers': False, 'has_blog': False, 'email': None}
    
    # Validation: Ensure URL has http/https
    if not url.startswith("http"):
        url = "http://" + url
        
    try:
        # Timeout requirement: 3 seconds per site
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, timeout=3, headers=headers)
        
        # Check status
        if response.status_code != 200:
            return data
            
        text = response.text.lower()
        
        # 1. Detect Careers
        if 'careers' in text or 'jobs' in text or 'join us' in text: 
            data['has_careers'] = True
            
        # 2. Detect Blog
        if 'blog' in text or 'news' in text: 
            data['has_blog'] = True
        
        # 3. Extract Email (Regex)
        # Matches typical emails but avoids common garbage (like image.png)
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        
        # Filter out "image" emails or garbage (basic filter)
        valid_emails = [e for e in emails if not e.endswith('.png') and not e.endswith('.jpg') and not e.endswith('.webp')]
        
        if valid_emails: 
            data['email'] = valid_emails[0] # Take the first valid one
        
        return data

    except Exception as e:
        # logging.warning(f"Failed to reach {url}: {e}")
        return data

def run_enrichment():
    try:
        conn = psycopg2.connect(DB_CONFIG)
        cursor = conn.cursor()
        
        # Get active companies that have a domain
        logging.info("Fetching companies to enrich...")
        cursor.execute("SELECT id, domain FROM companies WHERE is_active = true AND domain IS NOT NULL")
        companies = cursor.fetchall()
        
        total = len(companies)
        logging.info(f"Found {total} companies. Starting enrichment...")
        
        count = 0
        for comp_id, domain in companies:
            count += 1
            if count % 10 == 0:
                print(f"Processed {count}/{total}...")
                
            if not domain: continue
            
            # Run the check
            enrich_data = get_enrichment_data(domain)
            
            # Save to Database
            cursor.execute("""
                INSERT INTO company_web_enrichment (company_id, has_careers_page, has_blog, contact_email, scraped_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (company_id) DO UPDATE SET
                has_careers_page = EXCLUDED.has_careers_page,
                has_blog = EXCLUDED.has_blog,
                contact_email = EXCLUDED.contact_email,
                scraped_at = NOW()
            """, (comp_id, enrich_data['has_careers'], enrich_data['has_blog'], enrich_data['email']))
            conn.commit()

        logging.info("Enrichment Complete!")
    
    except Exception as e:
        logging.error(f"Enrichment Crashed: {e}")
    
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    run_enrichment()
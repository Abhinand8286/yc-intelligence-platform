import hashlib
import json
import asyncpg
import logging

# set up logging to see what happening in the console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_db_pool(db_url):

    return await asyncpg.create_pool(db_url)

async def process_company_record(pool, company_data):

    #decides if need to save a new snapshot or if nothing changed
    
    # 1. Create the fingerprint (Hash)
    # We sort keys so {"a":1, "b":2} is the same as {"b":2, "a":1}
    data_string = json.dumps(company_data, sort_keys=True).encode('utf-8')
    current_hash = hashlib.sha256(data_string).hexdigest()
    
    yc_slug = company_data['yc_company_id']
    
    async with pool.acquire() as conn:
        #check if the company already exists
        row = await conn.fetchrow("SELECT id, is_active FROM companies WHERE yc_company_id = $1", yc_slug)
        
        if not row:
            #new compny
            #insert into 'companies' table
            company_id = await conn.fetchval("""
                INSERT INTO companies (yc_company_id, name, domain, first_seen_at, last_seen_at, is_active)
                VALUES ($1, $2, $3, NOW(), NOW(), TRUE)
                RETURNING id
            """, yc_slug, company_data['name'], company_data['domain'])
            
            # Insert the first snapshot history
            await insert_snapshot(conn, company_id, company_data, current_hash)
            return "new"
            
        else:
            #existing cmpy
            company_id = row['id']
            
            # If it was marked inactive awake it
            if not row['is_active']:
                await conn.execute("UPDATE companies SET is_active = TRUE WHERE id = $1", company_id)
            
            # Check the LAST snapshot to see if anything changed
            last_snapshot = await conn.fetchrow("""
                SELECT data_hash FROM company_snapshots 
                WHERE company_id = $1 
                ORDER BY scraped_at DESC LIMIT 1
            """, company_id)
            
            if last_snapshot and last_snapshot['data_hash'] == current_hash:
                #noting changed
                #jst update the timestamp
                await conn.execute("UPDATE companies SET last_seen_at = NOW() WHERE id = $1", company_id)
                return "unchanged"
            
            else:
                #update detected
                #if smtng is diff 
                # We save a NEW snapshot to keep the history
                await insert_snapshot(conn, company_id, company_data, current_hash)
                
                await conn.execute("UPDATE companies SET last_seen_at = NOW() WHERE id = $1", company_id)
                return "updated"

async def insert_snapshot(conn, company_id, data, data_hash):
    """Helper to insert into the history table"""
    await conn.execute("""
        INSERT INTO company_snapshots 
        (company_id, batch, stage, description, location, tags, employee_range, scraped_at, data_hash)
        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8)
    """, 
    company_id, 
    data['batch'], 
    data['stage'], 
    data['description'], 
    data['location'], 
    json.dumps(data['tags']), # Store tags as a JSON list
    data['employee_range'], 
    data_hash)
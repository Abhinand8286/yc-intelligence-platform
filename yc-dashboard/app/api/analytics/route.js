import { Client } from 'pg';
import { NextResponse } from 'next/server';

const client = new Client({
  connectionString: "postgresql://postgres:12341@localhost:5432/postgres",
});
client.connect();

export async function GET() {
  try {
    // 1. Get Top Batches
    // FIX: Added ::int to count
    const batchRes = await client.query(`
      SELECT s.batch, COUNT(*)::int as count
      FROM company_snapshots s
      INNER JOIN (
          SELECT company_id, MAX(scraped_at) as max_date 
          FROM company_snapshots GROUP BY company_id
      ) latest ON s.company_id = latest.company_id AND s.scraped_at = latest.max_date
      WHERE s.batch IS NOT NULL AND s.batch != ''
      GROUP BY s.batch
      ORDER BY count DESC
      LIMIT 10;
    `);

    // 2. Get Stage Distribution
    // FIX: Added ::int to count
    const stageRes = await client.query(`
      SELECT s.stage, COUNT(*)::int as count
      FROM company_snapshots s
      INNER JOIN (
          SELECT company_id, MAX(scraped_at) as max_date 
          FROM company_snapshots GROUP BY company_id
      ) latest ON s.company_id = latest.company_id AND s.scraped_at = latest.max_date
      WHERE s.stage IS NOT NULL
      GROUP BY s.stage
      ORDER BY count DESC;
    `);

    // 3. Get Top Locations
    // FIX: Added ::int to count
    const locationRes = await client.query(`
      SELECT s.location, COUNT(*)::int as count
      FROM company_snapshots s
      INNER JOIN (
          SELECT company_id, MAX(scraped_at) as max_date 
          FROM company_snapshots GROUP BY company_id
      ) latest ON s.company_id = latest.company_id AND s.scraped_at = latest.max_date
      WHERE s.location IS NOT NULL AND s.location != ''
      GROUP BY s.location
      ORDER BY count DESC
      LIMIT 10;
    `);

    return NextResponse.json({
      batches: batchRes.rows,
      stages: stageRes.rows,
      locations: locationRes.rows
    });

  } catch (error) {
    console.error('Analytics API Error:', error);
    return NextResponse.json({ error: 'Server Error' }, { status: 500 });
  }
}
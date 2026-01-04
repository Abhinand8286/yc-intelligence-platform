import { Client } from 'pg';
import { NextResponse } from 'next/server';

const client = new Client({
  connectionString: "postgresql://postgres:12341@localhost:5432/postgres",
});
client.connect();

export async function GET() {
  try {
    const res = await client.query(`
      SELECT * FROM scrape_runs 
      ORDER BY started_at DESC 
      LIMIT 50
    `);
    
    return NextResponse.json(res.rows);
  } catch (error) {
    return NextResponse.json({ error: 'Server Error' }, { status: 500 });
  }
}
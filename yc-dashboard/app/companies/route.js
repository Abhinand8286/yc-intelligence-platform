import { Client } from 'pg';
import { NextResponse } from 'next/server';

const client = new Client({
  connectionString: "postgresql://postgres:12341@localhost:5432/postgres",
});
client.connect();

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page')) || 1;
    const limit = parseInt(searchParams.get('limit')) || 20;
    const search = searchParams.get('search') || '';
    
    const offset = (page - 1) * limit;

    let queryText = `
      SELECT 
        c.id, c.name, c.domain, s.batch, s.stage, s.tags, e.contact_email 
      FROM companies c
      LEFT JOIN company_snapshots s ON c.id = s.company_id
      LEFT JOIN company_web_enrichment e ON c.id = e.company_id
      WHERE s.scraped_at = (
        SELECT MAX(scraped_at) FROM company_snapshots WHERE company_id = c.id
      )
    `;

    const values = [];
    let counter = 1;

    if (search) {
      queryText += ` AND (c.name ILIKE $${counter} OR c.domain ILIKE $${counter})`;
      values.push(`%${search}%`);
      counter++;
    }

    queryText += ` ORDER BY c.id ASC LIMIT $${counter} OFFSET $${counter + 1}`;
    values.push(limit, offset);

    const res = await client.query(queryText, values);
    const countRes = await client.query('SELECT COUNT(*) FROM companies');
    
    return NextResponse.json({
      data: res.rows,
      pagination: {
        total: parseInt(countRes.rows[0].count),
        page: page,
        limit: limit
      }
    });

  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({ error: 'Server Error' }, { status: 500 });
  }
}
import { Client } from 'pg';
import { NextResponse } from 'next/server';

const client = new Client({
  connectionString: "postgresql://postgres:12341@localhost:5432/postgres",
});
client.connect();

export async function GET(request, { params }) {
  // FIX FOR NEXT.JS 15: We must 'await' params before using them
  const { id } = await params; 

  console.log(`🔍 API Request for Company ID: ${id}`); // Log to terminal for debugging

  try {
    // 1. Get Static Company Info + Web Enrichment
    const companyRes = await client.query(`
      SELECT c.*, e.has_careers_page, e.has_blog, e.contact_email 
      FROM companies c
      LEFT JOIN company_web_enrichment e ON c.id = e.company_id
      WHERE c.id = $1
    `, [id]);

    if (companyRes.rows.length === 0) {
      console.log("❌ Company not found in DB");
      return NextResponse.json({ error: 'Company not found' }, { status: 404 });
    }

    // 2. Get Snapshot History (The Timeline)
    const historyRes = await client.query(`
      SELECT * FROM company_snapshots 
      WHERE company_id = $1 
      ORDER BY scraped_at DESC
    `, [id]);

    return NextResponse.json({
      company: companyRes.rows[0],
      history: historyRes.rows
    });

  } catch (error) {
    console.error('Detail API Error:', error);
    return NextResponse.json({ error: 'Server Error' }, { status: 500 });
  }
}
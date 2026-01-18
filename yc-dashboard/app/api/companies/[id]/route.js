import { Client } from 'pg';
import { NextResponse } from 'next/server';

const client = new Client({
  connectionString: "postgresql://postgres:12341@localhost:5432/postgres",
});
client.connect();

export async function GET(request, { params }) {
  // Next.js App Router fix
  const { id } = await params;

  console.log(`🔍 API Request for Company ID: ${id}`);

  try {
    // 1️⃣ Company + Web Enrichment
    const companyRes = await client.query(`
      SELECT 
        c.*,
        e.has_careers_page,
        e.has_blog,
        e.contact_email
      FROM companies c
      LEFT JOIN company_web_enrichment e ON c.id = e.company_id
      WHERE c.id = $1
    `, [id]);

    if (companyRes.rows.length === 0) {
      return NextResponse.json({ error: 'Company not found' }, { status: 404 });
    }

    // 2️⃣ Snapshot History
    const historyRes = await client.query(`
      SELECT *
      FROM company_snapshots
      WHERE company_id = $1
      ORDER BY scraped_at DESC
    `, [id]);

    // 3️⃣ Change History (MANDATORY)
    const changesRes = await client.query(`
      SELECT change_type, old_value, new_value, detected_at
      FROM company_changes
      WHERE company_id = $1
      ORDER BY detected_at DESC
    `, [id]);

    // 4️⃣ Scores
    const scoresRes = await client.query(`
      SELECT momentum_score, stability_score, last_computed_at
      FROM company_scores
      WHERE company_id = $1
    `, [id]);

    // 5️⃣ AI Insights (Hugging Face)
    const aiRes = await client.query(`
      SELECT insight_type, content, model_name, generated_at
      FROM company_ai_insights
      WHERE company_id = $1
      ORDER BY generated_at DESC
    `, [id]);

    return NextResponse.json({
      company: companyRes.rows[0],
      history: historyRes.rows,
      changes: changesRes.rows,
      scores: scoresRes.rows[0] || null,
      ai_insights: aiRes.rows
    });

  } catch (error) {
    console.error('❌ Detail API Error:', error);
    return NextResponse.json({ error: 'Server Error' }, { status: 500 });
  }
}

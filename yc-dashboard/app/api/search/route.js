import { Client } from 'pg';
import { NextResponse } from 'next/server';

const client = new Client({
  connectionString: 'postgresql://postgres:12341@localhost:5432/postgres',
});
client.connect();

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);

    // Query params
    const q = searchParams.get('q') || '';
    const batch = searchParams.get('batch');
    const stage = searchParams.get('stage');
    const location = searchParams.get('location');
    const sort = searchParams.get('sort') || 'relevance'; // relevance | momentum
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '20');
    const offset = (page - 1) * limit;

    // Base SQL
    let whereClauses = [];
    let values = [];
    let idx = 1;

    if (q) {
      whereClauses.push(
        `search_vector @@ plainto_tsquery('english', $${idx++})`
      );
      values.push(q);
    }

    if (batch) {
      whereClauses.push(`c.id IN (
        SELECT company_id FROM company_snapshots WHERE batch = $${idx++}
      )`);
      values.push(batch);
    }

    if (stage) {
      whereClauses.push(`c.id IN (
        SELECT company_id FROM company_snapshots WHERE stage = $${idx++}
      )`);
      values.push(stage);
    }

    if (location) {
      whereClauses.push(`c.id IN (
        SELECT company_id FROM company_snapshots WHERE location ILIKE $${idx++}
      )`);
      values.push(`%${location}%`);
    }

    const whereSQL =
      whereClauses.length > 0 ? `WHERE ${whereClauses.join(' AND ')}` : '';

    // Sorting
    let orderSQL;
    if (sort === 'momentum') {
      orderSQL = `ORDER BY cs.momentum_score DESC NULLS LAST`;
    } else {
      orderSQL = q
        ? `ORDER BY ts_rank(search_vector, plainto_tsquery('english', $1)) DESC`
        : `ORDER BY c.last_seen_at DESC`;
    }

    const query = `
      SELECT
        c.id,
        c.name,
        c.domain,
        c.is_active,
        cs.momentum_score,
        cs.stability_score
      FROM companies c
      LEFT JOIN company_scores cs ON cs.company_id = c.id
      ${whereSQL}
      ${orderSQL}
      LIMIT ${limit} OFFSET ${offset};
    `;

    const result = await client.query(query, values);

    return NextResponse.json({
      page,
      limit,
      results: result.rows,
    });

  } catch (err) {
    console.error('Search API Error:', err);
    return NextResponse.json({ error: 'Server error' }, { status: 500 });
  }
}

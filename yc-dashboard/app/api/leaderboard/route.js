import { Client } from 'pg';
import { NextResponse } from 'next/server';

const client = new Client({
  connectionString: 'postgresql://postgres:12341@localhost:5432/postgres',
});
client.connect();

export async function GET() {
  try {
    // 1️⃣ Top companies by momentum score
    const topMomentum = await client.query(`
      SELECT
        c.id,
        c.name,
        c.domain,
        cs.momentum_score
      FROM company_scores cs
      JOIN companies c ON c.id = cs.company_id
      ORDER BY cs.momentum_score DESC
      LIMIT 10;
    `);

    // 2️⃣ Most stable companies
    const mostStable = await client.query(`
      SELECT
        c.id,
        c.name,
        c.domain,
        cs.stability_score
      FROM company_scores cs
      JOIN companies c ON c.id = cs.company_id
      ORDER BY cs.stability_score DESC
      LIMIT 10;
    `);

    // 3️⃣ Recently changed companies
    const recentlyChanged = await client.query(`
      SELECT DISTINCT ON (cc.company_id)
        c.id,
        c.name,
        c.domain,
        cc.change_type,
        cc.detected_at
      FROM company_changes cc
      JOIN companies c ON c.id = cc.company_id
      ORDER BY cc.company_id, cc.detected_at DESC
      LIMIT 10;
    `);

    return NextResponse.json({
      top_momentum: topMomentum.rows,
      most_stable: mostStable.rows,
      recently_changed: recentlyChanged.rows,
    });

  } catch (error) {
    console.error('Leaderboard API Error:', error);
    return NextResponse.json(
      { error: 'Server Error' },
      { status: 500 }
    );
  }
}

import { Pool } from "pg";
import { NextResponse } from "next/server";

const pool = new Pool({
  connectionString: process.env.DB_URL,
});

export async function GET() {
  try {
    // ---------------------------
    // 1️⃣ Fastest Growing Tags
    // (from latest snapshot only)
    // ---------------------------
    const tagsRes = await pool.query(`
      SELECT
        tag,
        COUNT(*)::int AS occurrences
      FROM (
        SELECT
          jsonb_array_elements_text(s.tags) AS tag
        FROM company_snapshots s
        INNER JOIN (
          SELECT company_id, MAX(scraped_at) AS max_date
          FROM company_snapshots
          GROUP BY company_id
        ) latest
        ON s.company_id = latest.company_id
        AND s.scraped_at = latest.max_date
        WHERE s.tags IS NOT NULL
      ) t
      GROUP BY tag
      ORDER BY occurrences DESC
      LIMIT 10;
    `);

    // ----------------------------------
    // 2️⃣ Locations with most companies
    // ----------------------------------
    const locationsRes = await pool.query(`
      SELECT
        s.location,
        COUNT(*)::int AS count
      FROM company_snapshots s
      INNER JOIN (
        SELECT company_id, MAX(scraped_at) AS max_date
        FROM company_snapshots
        GROUP BY company_id
      ) latest
      ON s.company_id = latest.company_id
      AND s.scraped_at = latest.max_date
      WHERE s.location IS NOT NULL AND s.location != ''
      GROUP BY s.location
      ORDER BY count DESC
      LIMIT 10;
    `);

    // ----------------------------------
    // 3️⃣ Stage Transition Trends
    // ----------------------------------
    const stageRes = await pool.query(`
      SELECT
        detected_at::date AS date,
        old_value || ' → ' || new_value AS transition,
        COUNT(*)::int AS count
      FROM company_changes
      WHERE change_type = 'STAGE_CHANGE'
      GROUP BY date, transition
      ORDER BY date DESC
      LIMIT 30;
    `);

    return NextResponse.json({
      fastest_growing_tags: tagsRes.rows,
      top_locations: locationsRes.rows,
      stage_transitions: stageRes.rows,
    });

  } catch (error) {
    console.error("Trends API Error:", error);
    return NextResponse.json(
      { error: "Failed to load trends" },
      { status: 500 }
    );
  }
}

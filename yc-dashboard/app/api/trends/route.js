import { Client } from "pg";
import { NextResponse } from "next/server";

const client = new Client({
  connectionString: "postgresql://postgres:12341@localhost:5432/postgres",
});

client.connect();

export async function GET() {
  try {
    // 1️⃣ Fastest Growing Tags
    const tagsRes = await client.query(`
      SELECT
        jsonb_array_elements_text(tags) AS tag,
        COUNT(*) AS occurrences
      FROM company_snapshots
      GROUP BY tag
      ORDER BY occurrences DESC
      LIMIT 10
    `);

    // 2️⃣ Locations with Most New Companies
    const locationsRes = await client.query(`
      SELECT
        location,
        COUNT(*) AS new_companies
      FROM company_snapshots
      GROUP BY location
      ORDER BY new_companies DESC
      LIMIT 10
    `);

    // 3️⃣ Stage Transition Trends
    const stageRes = await client.query(`
      SELECT
        detected_at::date AS date,
        old_value || ' → ' || new_value AS transition,
        COUNT(*) AS count
      FROM company_changes
      WHERE change_type = 'STAGE_CHANGE'
      GROUP BY date, transition
      ORDER BY date DESC
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

import { NextResponse } from "next/server";
import { Pool } from "pg";
import OpenAI from "openai";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { companyId, question } = body;

    if (!companyId || !question) {
      return NextResponse.json(
        { error: "companyId and question are required" },
        { status: 400 }
      );
    }

    // Fetch company
    const companyRes = await pool.query(
      `
      SELECT c.name, s.description
      FROM companies c
      JOIN company_snapshots s ON s.company_id = c.id
      WHERE c.id = $1
      ORDER BY s.scraped_at DESC
      LIMIT 1
      `,
      [companyId]
    );

    if (companyRes.rows.length === 0) {
      return NextResponse.json(
        { error: "Company not found" },
        { status: 404 }
      );
    }

    const company = companyRes.rows[0];

    // Fetch changes
    const changesRes = await pool.query(
      `
      SELECT change_type, old_value, new_value
      FROM company_changes
      WHERE company_id = $1
      ORDER BY detected_at DESC
      LIMIT 5
      `,
      [companyId]
    );

    // Fetch scores
    const scoresRes = await pool.query(
      `
      SELECT momentum_score, stability_score
      FROM company_scores
      WHERE company_id = $1
      `,
      [companyId]
    );

    const scores = scoresRes.rows[0];

    const prompt = `
You are an analyst assistant for a YC company intelligence system.

Company Name:
${company.name}

Company Description:
${company.description}

Recent Changes:
${
  changesRes.rows.length === 0
    ? "No recent changes."
    : changesRes.rows
        .map(
          (c) => `- ${c.change_type}: ${c.old_value} → ${c.new_value}`
        )
        .join("\n")
}

Scores:
- Momentum: ${scores?.momentum_score ?? "N/A"}
- Stability: ${scores?.stability_score ?? "N/A"}

User Question:
"${question}"

Rules:
- Do not invent facts
- Answer in 4–6 sentences
`;

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: prompt }],
      temperature: 0.2,
    });

    return NextResponse.json({
      answer: completion.choices[0].message.content,
    });

  } catch (err) {
    console.error("AI ERROR:", err);
    return NextResponse.json(
      { error: "Failed to contact AI service." },
      { status: 500 }
    );
  }
}

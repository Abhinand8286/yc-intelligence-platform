import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { companyId, question } = await req.json();

    if (!companyId || !question) {
      return NextResponse.json(
        { error: "companyId and question are required" },
        { status: 400 }
      );
    }

    // 🔁 Proxy request to FastAPI (Ollama + RAG lives there)
    const res = await fetch(
      `http://127.0.0.1:8000/api/companies/${companyId}/explain`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      }
    );

    if (!res.ok) {
      const errText = await res.text();
      return NextResponse.json(
        { error: errText || "AI service failed" },
        { status: res.status }
      );
    }

    const data = await res.json();

    return NextResponse.json({
      answer: data.answer,
    });

  } catch (err) {
    console.error("AI ROUTE ERROR:", err);
    return NextResponse.json(
      { error: "Failed to contact AI service." },
      { status: 500 }
    );
  }
}

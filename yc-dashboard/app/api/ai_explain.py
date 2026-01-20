from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

from app.db_logic import get_db_pool
from app.ai_intelligence import generate_company_explanation

router = APIRouter()

class ExplainRequest(BaseModel):
    question: str


@router.post("/companies/{company_id}/explain")
async def explain_company(company_id: int, payload: ExplainRequest):

    db_url = os.getenv("DB_URL")
    if not db_url:
        raise HTTPException(status_code=500, detail="DB_URL not set")

    pool = await get_db_pool(db_url)

    async with pool.acquire() as conn:
        company = await conn.fetchrow("""
            SELECT c.name, s.description, s.stage, s.tags
            FROM companies c
            JOIN company_snapshots s ON s.company_id = c.id
            WHERE c.id = $1
            ORDER BY s.scraped_at DESC
            LIMIT 1
        """, company_id)

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        changes = await conn.fetch("""
            SELECT change_type, old_value, new_value
            FROM company_changes
            WHERE company_id = $1
            ORDER BY detected_at DESC
            LIMIT 5
        """, company_id)

        scores = await conn.fetchrow("""
            SELECT momentum_score, stability_score
            FROM company_scores
            WHERE company_id = $1
        """, company_id)

    explanation = generate_company_explanation(
        company=dict(company),
        changes=[dict(c) for c in changes],
        scores=dict(scores) if scores else {},
        question=payload.question
    )

    if not explanation:
        return {
            "answer": "AI could not generate an explanation at this time."
        }

    return {"answer": explanation}

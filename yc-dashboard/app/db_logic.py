import hashlib
import json
import asyncpg
import logging
from datetime import datetime

from app.ai_intelligence import generate_company_explanation

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------
# DB Pool
# -----------------------------
async def get_db_pool(db_url):
    return await asyncpg.create_pool(db_url)


# -----------------------------
# Helpers
# -----------------------------
def compute_hash(data: dict) -> str:
    return hashlib.sha256(
        json.dumps(data, sort_keys=True).encode("utf-8")
    ).hexdigest()


def detect_changes(old, new):
    changes = []

    if old["stage"] != new["stage"]:
        changes.append(("STAGE_CHANGE", old["stage"], new["stage"]))

    if old["location"] != new["location"]:
        changes.append(("LOCATION_CHANGE", old["location"], new["location"]))

    if set(old["tags"]) != set(new["tags"]):
        changes.append(("TAG_CHANGE", json.dumps(old["tags"]), json.dumps(new["tags"])))

    if old["description"] != new["description"]:
        changes.append(("DESCRIPTION_CHANGE", old["description"], new["description"]))

    return changes


def compute_scores(change_count, days_since_last_change):
    momentum = change_count * 2
    stability = max(0, 100 - days_since_last_change)
    return momentum, stability


# -----------------------------
# Search Vector Update
# -----------------------------
async def update_search_vector(conn, company_id):
    await conn.execute("""
        UPDATE companies c
        SET search_vector =
            setweight(to_tsvector('english', coalesce(c.name, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(s.description, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(s.tags::text, '')), 'C')
        FROM company_snapshots s
        WHERE s.company_id = c.id
          AND s.company_id = $1
          AND s.scraped_at = (
              SELECT MAX(scraped_at)
              FROM company_snapshots
              WHERE company_id = $1
          );
    """, company_id)


# -----------------------------
# Core Logic
# -----------------------------
async def process_company_record(pool, company_data):

    current_hash = compute_hash(company_data)
    yc_slug = company_data["yc_company_id"]

    async with pool.acquire() as conn:
        async with conn.transaction():

            row = await conn.fetchrow(
                "SELECT id, is_active FROM companies WHERE yc_company_id = $1",
                yc_slug
            )

            # =============================
            # NEW COMPANY
            # =============================
            if not row:
                company_id = await conn.fetchval("""
                    INSERT INTO companies
                    (yc_company_id, name, domain, first_seen_at, last_seen_at, is_active)
                    VALUES ($1, $2, $3, NOW(), NOW(), TRUE)
                    RETURNING id
                """, yc_slug, company_data["name"], company_data["domain"])

                snapshot_id = await insert_snapshot(
                    conn, company_id, company_data, current_hash
                )

                await update_search_vector(conn, company_id)

                await conn.execute("""
                    INSERT INTO company_scores (company_id, momentum_score, stability_score)
                    VALUES ($1, 0, 100)
                """, company_id)

                insight = generate_company_explanation(
                    company=company_data,
                    changes=[],
                    scores={"momentum": 0, "stability": 100}
                )

                if insight is None:
                    insight = "AI summary not available."


                # ✅ SAFE AI INSERT
                    await conn.execute("""
                        INSERT INTO company_ai_insights
                        (company_id, insight_type, content, model_name, snapshot_id)
                        VALUES ($1, 'SUMMARY', $2, 'disabled', $3)
                    """, company_id, insight, "openai" if insight != "AI summary not available." else "disabled" , snapshot_id)

                return "new"

            # =============================
            # EXISTING COMPANY
            # =============================
            company_id = row["id"]

            if not row["is_active"]:
                await conn.execute(
                    "UPDATE companies SET is_active = TRUE WHERE id = $1",
                    company_id
                )

            last_snapshot = await conn.fetchrow("""
                SELECT id, stage, location, description, tags, scraped_at, data_hash
                FROM company_snapshots
                WHERE company_id = $1
                ORDER BY scraped_at DESC
                LIMIT 1
            """, company_id)

            # =============================
            # BASELINE SNAPSHOT
            # =============================
            if last_snapshot is None:
                snapshot_id = await insert_snapshot(
                    conn, company_id, company_data, current_hash
                )

                await update_search_vector(conn, company_id)

                await conn.execute("""
                    INSERT INTO company_scores (company_id, momentum_score, stability_score)
                    VALUES ($1, 0, 100)
                    ON CONFLICT (company_id) DO NOTHING
                """, company_id)

                insight = generate_company_explanation(
                    company=company_data,
                    changes=[],
                    scores={"momentum": 0, "stability": 100}
                )

                if insight:
                    await conn.execute("""
                        INSERT INTO company_ai_insights
                        (company_id, insight_type, content, model_name, snapshot_id)
                        VALUES ($1, 'SUMMARY', $2, 'disabled', $3)
                    """, company_id, insight, snapshot_id)

                await conn.execute(
                    "UPDATE companies SET last_seen_at = NOW() WHERE id = $1",
                    company_id
                )

                return "updated"

            # =============================
            # NO CHANGE
            # =============================
            if last_snapshot["data_hash"] == current_hash:
                await conn.execute(
                    "UPDATE companies SET last_seen_at = NOW() WHERE id = $1",
                    company_id
                )
                return "unchanged"

            # =============================
            # CHANGE DETECTED
            # =============================
            snapshot_id = await insert_snapshot(
                conn, company_id, company_data, current_hash
            )

            await update_search_vector(conn, company_id)

            old_data = {
                "stage": last_snapshot["stage"],
                "location": last_snapshot["location"],
                "description": last_snapshot["description"],
                "tags": json.loads(last_snapshot["tags"]),
            }

            changes = detect_changes(old_data, company_data)

            for ctype, old, new in changes:
                await conn.execute("""
                    INSERT INTO company_changes
                    (company_id, change_type, old_value, new_value, detected_at)
                    VALUES ($1, $2, $3, $4, NOW())
                """, company_id, ctype, old, new)

            days_since = (datetime.utcnow() - last_snapshot["scraped_at"]).days
            momentum, stability = compute_scores(len(changes), days_since)

            await conn.execute("""
                INSERT INTO company_scores
                (company_id, momentum_score, stability_score, last_computed_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (company_id)
                DO UPDATE SET
                    momentum_score = EXCLUDED.momentum_score,
                    stability_score = EXCLUDED.stability_score,
                    last_computed_at = NOW()
            """, company_id, momentum, stability)

            insight = generate_company_explanation(
                company=company_data,
                changes=changes,
                scores={"momentum": momentum, "stability": stability}
            )

            if insight:
                await conn.execute("""
                    INSERT INTO company_ai_insights
                    (company_id, insight_type, content, model_name, snapshot_id)
                    VALUES ($1, 'SUMMARY', $2, 'disabled', $3)
                """, company_id, insight, snapshot_id)

            await conn.execute(
                "UPDATE companies SET last_seen_at = NOW() WHERE id = $1",
                company_id
            )

            return "updated"


# -----------------------------
# Snapshot Insert
# -----------------------------
async def insert_snapshot(conn, company_id, data, data_hash):
    return await conn.fetchval("""
        INSERT INTO company_snapshots
        (company_id, batch, stage, description, location, tags,
         employee_range, scraped_at, data_hash)
        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), $8)
        RETURNING id
    """,
    company_id,
    data["batch"],
    data["stage"],
    data["description"],
    data["location"],
    json.dumps(data["tags"]),
    data["employee_range"],
    data_hash)

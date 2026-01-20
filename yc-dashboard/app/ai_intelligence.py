import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3"   # low RAM, fast, self-hosted

def generate_company_explanation(company, changes, scores, question):
    """
    Self-hosted LLM using Ollama (phi3)
    RAG via prompt injection
    NO external APIs
    """

    # ---------- Format changes cleanly ----------
    if changes:
        changes_text = "\n".join(
            f"- {c['change_type']}: {c['old_value']} → {c['new_value']}"
            for c in changes
        )
    else:
        changes_text = "No recent changes."

    # ---------- Safe score access ----------
    momentum = scores.get("momentum_score", "N/A") if scores else "N/A"
    stability = scores.get("stability_score", "N/A") if scores else "N/A"

    # ---------- RAG Prompt ----------
    prompt = f"""
You are an internal AI analyst for a YC company intelligence system.

Company Name:
{company.get('name')}

Description:
{company.get('description')}

Stage:
{company.get('stage')}

Tags:
{company.get('tags')}

Recent Changes:
{changes_text}

Scores:
- Momentum: {momentum}
- Stability: {stability}

User Question:
"{question}"

Rules:
- Use ONLY the information above
- Do NOT guess or hallucinate
- Be factual and concise
- Answer in 3–5 sentences
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        if response.status_code != 200:
            print("Ollama HTTP error:", response.text)
            return None

        data = response.json()
        return data.get("response", "").strip() or None

    except Exception as e:
        print("Ollama execution error:", e)
        return None

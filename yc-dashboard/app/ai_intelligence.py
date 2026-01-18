from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_company_explanation(company, changes, scores, question):
    """
    Safe AI summary generator.
    Returns None if API key is missing or AI fails.
    """

    if not os.getenv("OPENAI_API_KEY"):
        return None  # 🔒 LLM disabled safely

    prompt = f"""
Company Name: {company.get('name')}
Description: {company.get('description')}
Stage: {company.get('stage')}
Tags: {company.get('tags')}

Recent Changes:
{changes}

Scores:
Momentum: {scores.get('momentum')}
Stability: {scores.get('stability')}

User Question:
{question}

Task:
Answer the user's question using ONLY the provided company data.
Be factual and concise.
If the data does not contain the answer, say "Not enough data available."
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data analyst summarizing YC companies."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("AI Error:", e)
        return None

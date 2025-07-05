import os
import json
import re
import requests
# API key from env
api_key = os.getenv("PERPLEXITY_API_KEY")

if not api_key:
    raise EnvironmentError("PERPLEXITY_API_KEY not set")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

#read the claims from txt document and apply article number 5
article_number=5
claim_article_list = []
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
resolved_path = os.path.abspath(os.path.join(BASE_DIR, "data", "test3.txt"))
with open(resolved_path, "r", encoding="utf-8") as f:
    claims = f.readlines()
    for claim in claims:
        claim = claim.strip()
        if claim:  # Ensure the line is not empty
            claim_article_list.append((claim, article_number))  # Using 5 articles for each claim
            # Define the system message for the GPT-4o model
            print(f"Claim: {claim}, Articles:{article_number} ")
            print(f"Processing claim: {claim}")
            print(f"Using {article_number} articles for each claim.")

# system prompt
system_message = {
    "role": "system",
    "content": """
You are a scientific assistant. Evaluate a scientific claim using evidence from EXACTLY 5 different scientific articles.

Respond ONLY with a JSON object **exactly** matching this format (no extra text):

{
  "summary": "A paragraph with exactly 5 sentences. Each sentence must directly copy the 'claim' field from one of the subclaims (without any rewording), and include an <a> tag linking to the 'url' of that subclaim."
  "accuracy": "An accuracy label: True, Mostly True, Partially True, or False.",
  "reason_for_accuracy": "A concise explanation of the accuracy label.",
  "subclaims": [
    {
      "claim": "the specific subclaim which is included in the summary.(MUST be 5 claims from EXACTLY 5 different sources).",
      "title": "Supporting article title for the claim which is included in the summary.",
      "authors": "Article authors.",
      "section": "Article section where evidence appears.",
      "paragraph": "Full paragraph with relevant evidence.",
      "url": "Link to the article.",
      "venue": "Publication venue.",
      "year": "Year of publication.",
      "contribution": "conditionally supports / completely supports / conditionally refutes / completely refutes",
      "relevant_sentence": "Sentence supporting or refuting subclaim.",
      "supporting_assumptions": ["Assumption 1", "Assumption 2"],
      "refuting_assumptions": ["Assumption 1", "Assumption 2"],
      "credibility_score": "Citation count, impact factor, (any numeric metric)."
    }
  ]
}

Do NOT include any text outside this JSON.
"""
}

results = []

for claim, num_articles in claim_article_list:
    user_message = {
        "role": "user",
        "content": json.dumps({
            "claim": claim,
            "articles": str(num_articles)
        })
    }

    payload = {
        "model": "sonar-pro",
        "messages": [system_message, user_message]
    }

    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )
        response.raise_for_status()
        res_json = response.json()

        text = res_json["choices"][0]["message"]["content"].strip()

        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in the response")

        data = json.loads(json_match.group(0))

        results.append({
            "claim": claim,
            "num_articles": num_articles,
            "output": data
        })

    except Exception as e:
        results.append({
            "claim": claim,
            "num_articles": num_articles,
            "error": str(e),
            "raw_response": text if 'text' in locals() else None
        })

base_dir = os.path.dirname(os.path.abspath(__file__))
JSON_OUTPUT_PATH = os.path.join(base_dir, 'sonar_pro_outputs3.json')

with open(JSON_OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("✅ Results saved to sonar_pro_outputs.json")

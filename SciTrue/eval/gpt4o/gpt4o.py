import os
import json
import re
import openai
from generations.parsing_and_saving_functions import clean_and_convert
api_key = os.getenv("OPEN_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY not set")
openai.api_key = api_key

#read the claims from txt document and apply article number 5
article_number=5
claim_article_list = []

# === CONFIG: Paths to your JSON output files ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

resolved_path = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "test3.txt"))
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
         

system_message = {
    "role": "system",
    "content": """
You are a scientific assistant. Evaluate a scientific claim using evidence from EXACTLY 5 different scientific articles.

Respond ONLY with a JSON object **exactly** matching this format (no extra text):

{
  "summary": "A paragraph summarising the evidence related to the claim, each of sentences in summary MUST include a HTML <a> tags to link to the sources, formatted as: <a href='https://...'>Article Title</a>" ,
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
            "number of articles": str(num_articles)
        })
    }
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-search-preview",
            messages=[system_message, user_message],
            max_tokens=16384,
            response_format={"type": "text"},  # Must be "text" with this model
            web_search_options={"search_context_size": "high"}
        )
        text = response.choices[0].message["content"].strip()
        print(user_message['content'])
        # Extract JSON from GPT output text
        json_string = text.replace('```json', '').replace('```', '').strip()
        json_string = re.sub(r',\s*([\]}])', r'\1', json_string)
        json_match = re.search(r"\{.*\}", json_string, re.DOTALL)
        json_match=re.sub(r"^```json\s*|```$", "", text.strip(), flags=re.DOTALL)
        
        if not json_match:
            raise ValueError("No JSON object found in the response")

        # json_str = json_match.group(0)
       

        data = json.loads(json_match)

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

with open("eval/gpt4o/gpt4o_results3.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("✅ Results saved to gpt4o_outputs.json")

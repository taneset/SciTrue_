
#%%
def make_claim_refinement_query(claim: str) -> str:
   
    instruction = """You are part of a scientific retrieval system. Given an input, do the following:

1. If the input is a scientific claim, rephrase it clearly and concisely (max 130 characters).
2. If the input is a question, unclear, too vague return "None".

Return this JSON format:
{
  "original_query": "...",
  "revised_query": "..."
}
"""

    prompt= instruction + f'original_query: {claim}'


    return prompt




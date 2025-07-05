#%%
import sys
import os
# Importing custom modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generations.evidence_synthesis import main_evidence_list
from generations.claim_refinement import get_revised_query
import asyncio
#%%
import asyncio

def make_report_query(claim: str, k: int) -> str:
    hint = None
    prompt_grounding = f'Claim: "{claim}"'
    revised_query = asyncio.run(get_revised_query(claim))
    if len(revised_query) > 6:
        raw_data = main_evidence_list(claim=revised_query, k=k)
    else:
        return None, False, "The claim is not a scientific claim or does not make any sense, please try again with a different claim."
    # raw_data = main_evidence_list(claim=revised_query, k=k)
    data = raw_data[raw_data['relevance'] == "yes"]

    # Extract necessary fields
    authors = list(data['authors'])
    year = list(data['year'])
    link = list(data['url'])
    evidence = list(data['relevant sentence'])
    label = list(data['label'])
    positive_assumptions = list(data['supporting assumptions'])
    negative_assumptions = list(data['refuting assumptions'])

    # Check if data is insufficient
    if len(data) < k:
        if len(data) <= 2:
            return None, False, "Sorry, we couldn't find enough articles for this claim. Please try rephrasing or using a different claim"
        if len(data) > 2:
            hint = f"Only {len(data)} articles were found (less than the requested {k}). Proceeding with the available articles."
    evidence_content_list = []

    # Iterate through the first k relevant pieces of evidence
    for lbl, evd, athr, yr, lnk, pos_assm, neg_assm in zip(
        label[:k], evidence[:k], authors[:k], year[:k], link[:k], 
        positive_assumptions[:k], negative_assumptions[:k]
    ):
        # Determine label description
        if "conditional" in lbl:
            display_lbl = "Evidence that may partially support or refute the claim"
        elif "completely" in lbl:
            display_lbl = "Evidence that may support or refute the claim"
        else:
            display_lbl = ""

        # Format assumptions if they exist
        assumptions_text = ""
        if pos_assm:
            assumptions_text += f"\n  - **Positive assumptions:** {', '.join(pos_assm)}"
        if neg_assm:
            assumptions_text += f"\n  - **Negative assumptions:** {', '.join(neg_assm)}"

        # Compile evidence entry
        evidence_entry = (
            f"{display_lbl}: {evd}\n\n"
            f"Assumptions of the evidence:{assumptions_text}\n"
            f"Authors: {athr}, Year: {yr}, Link: {lnk}"
        )

        evidence_content_list.append(evidence_entry)

    # Combine all evidence
    evidence_content_str = "\n\n".join(evidence_content_list)
    prompt_grounding += f"\n\nEvidence:\n{evidence_content_str}"

    # Prompt instruction
    prompt_instruction = """
    You are given a claim or question along with a set of evidence sentences sourced from published papers. Each piece of evidence may either **support or refute** the claim, either partially or completely.

    Your task is to:

    1. **Create an executive summary** that synthesizes all provided evidence and their stance (supporting or refuting).
    2. **Cite each sentence of evidence in the summary exactly once**, and integrate it **coherently and accurately**.
    3. Format each citation as an **HTML hyperlink** using the structure:
    `<a href="URL">FirstAuthor et al. (Year)</a>` — use the first author's name followed by "et al." and the year from the citation data.
    4. Ensure that **each citation is used only once**, and no extra or duplicate citations are introduced.
    5. **Assess the faithfulness of the claim** based solely on the provided evidence (including both supporting and refuting parts and assumptions).

    *Example citation formatting in a sentence*:
    "The findings align with previous results  (<a href='https://api.semanticscholar.org/CorpusId:269813687'>FirstAuthor et al, year</a>)..."

    ---

### Your output must strictly follow this structured JSON format:

{
  "claim": "...", 
  "executive summary": "...(HTML-formatted summary using correctly formatted, clickable citations)", 
  "accuracy": "x/100",  
  "reason for accuracy": "..."( explain why you assigned the score and include one of True, Mostly True, Partially True, False in your reasoning, based on the evidence provided. This should be a concise explanation of your assessment of the claim's faithfulness to the evidence)
}
"""


    prompt = f"{prompt_instruction}\n{prompt_grounding}"

    return prompt, True, hint

    
# %%
# claim = "reinforcement learning require too much data"
# k = 5
# %%

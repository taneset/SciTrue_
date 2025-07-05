#%%
import asyncio
from typing import List
import nest_asyncio

# Apply the nest_asyncio patch to allow nested event loops
nest_asyncio.apply()


async def make_evidence_list_query(claim: str, title: str, paragraph: str, abstract: str) -> str:
    q1 = f'Consider the claim: {claim}.'

    q2 = """
Read the following scientific paragraph and answer:

Q1. Are the claim and the paragraph related (ONLY yes or no)?

Q2. What evidence in the paragraph addresses the claim?
Classify the type:
  Type 1: Statement declaring something is better.
  Type 2: Proposal of something new.
  Type 3: Description of a new finding or cause-effect relationship.
  Type 4: Other.

Q3. Does the evidence support or refute the claim? Specify strength and conditions:
- "completely supports"
- "conditionally supports"
- "completely refutes"
- "conditionally refutes"

Q4. What is the function of the relevant sentence text toward the claim?  
Pick ONLY ONE:

- "Main Finding": The sentence is a main result or claim of this paper.
- "Background": The sentence is context, prior work, or used as evaluation material but not a result of this paper.
- "Limitation": Limitation, caveat, or uncertainty.

Briefly explain your choice for Q4.

Q5. How directly do the title AND abstract relate to the claim?  
Assign one value — "strong", "medium", or "weak" — and give a short reason referring to BOTH the title and abstract.
- "strong": Title and/or abstract are directly about the claim.
- "medium": Broadly on the topic but not direct.
- "weak": Only indirectly related.
"""

    q3 = f"""
Paragraph: {paragraph}

Title: {title}
Abstract: {abstract}
"""

    q4 = """
Format your output as:
{
 "Ans 1": "yes" or "no",
 "relevant sentence text": "...",
 "type of claim": "type 1 / type 2 / type 3 / type 4",
 "supports or refutes claim": "conditionally supports / completely supports / conditionally refutes / completely refutes",
 "assumptions and conditions mentioned in the text when supporting the claim": ["..."],
 "assumptions and conditions mentioned in the text when refuting the claim": ["..."],
 "relevant sentence text function": "Main Finding / Background / Limitation",
 "function_reason": "Very short reason for the label, explaining why this sentence IS or IS NOT a main outcome of the current paper.",
 "relation": "strong / medium / weak",
 "relation_reason": Very short justification based on how the title and abstract matches, covers, or only loosely relates to the claim"
}
"""

    return q1 + q2 + q3 + q4
import asyncio
from typing import List

async def make_evidence_list_prompts(claim: str, paragraphs: List[str], titles: List[str], abstracts: List[str]) -> List[str]:
    tasks = []
    for title, paragraph, abstract in zip(titles, paragraphs, abstracts):  
        task = asyncio.create_task(make_evidence_list_query(claim, title, paragraph, abstract))  
        tasks.append(task)

    # Gather results from all tasks
    results = await asyncio.gather(*tasks)
    return results

#%%
# if __name__ == "__main__":
#     # Example claim
#     claim = "Model editing improves performance in NLP tasks"

#     # Example data containing titles and paragraphs
#     paragraphs = [
#         "In this paper, we propose a novel approach for improving the performance of NLP models through model editing. We extensively utilize deletion, addition, templatization, and synonym substitution to teach the model to make these changes.",
#         "Our research explores various deep learning techniques for NLP tasks. One promising approach involves fine-tuning pre-trained models using edit operations such as deletion, addition, and substitution."
#     ]
#     titles = ["Enhancing NLP Models with Edit Operations", "Deep Learning Techniques for NLP"]

#     # Generate prompts asynchronously
#     generated_prompts = asyncio.run(make_evidence_list_prompts(claim, paragraphs, titles))

#     # Print the generated prompts
#     print(generated_prompts)

# %%

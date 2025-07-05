
#%%
def make_claim_extraction_query(text: str, claim:str) -> str:
   
    instruction = """Can you extract claims made in the following text without making any reference in the claim and find the matching paper id that claims are made in? Please also assign an accuracy score out of 100, along with the reason for the assigned score, by considering sources outside of the given text.
Can you also provide whether the each claim corrobrates or contrasts the given query?



Your output should be this list:
[
    {
        "claim": "...",
        "CorpusId": "...",
        "accuracy": "...",
        "reason for accuracy": "...",
        "contribution": "corroborating/partially corroborating/slightly corroborating/contrasting/ partially contrasting/slightly contrasting/inconclusive",
    },
    {
        "claim": "...",
        "CorpusId": "...",
        "accuracy": "...",
        "reason for accuracy: "...",
        "contribution": "corroborating/partially corroborating/slightly corroborating/contrasting/ partially contrasting/slightly contrasting/inconclusive",
    }
]
"""
 
    text=text
    claim=claim
#     
    prompt= instruction + f'/n text: {text}/n query: {claim}'


    return prompt
# %%
# text=""" The claim that SSDs are more expensive than HDDs is nuanced and can be supported or refuted depending on the context. 
#  According to [Qianbin Xia (2017)](https://api.semanticscholar.org/CorpusId:208963067), SSDs offer a good compromise among performance, capacity, and cost, suggesting that while they may be more expensive, their performance benefits could justify the cost. 
#  [M. Praveen, Zinan Liu, and Kumar Reddy (2022)](https://api.semanticscholar.org/CorpusId:250413695) highlight that hard drives are significantly slower than SSDs, which could imply that the higher cost of SSDs is offset by their superior speed. 
# [Adrià Armejach, Adrián Cristal, Osman Unsal, Naveed Mustafa, and Ozcan Ozturk (2016)](https://api.semanticscholar.org/CorpusId:17794134) mention the use of high-end SSDs as regular disk storage, indicating that SSDs are being adopted despite their cost. 
#  Finally, [Horst Simon and Hongyuan Zha (1997)](https://api.semanticscholar.org/CorpusId:118134702) note that hard disks are the most popular secondary storage and are slow, which could be a factor in their lower cost compared to SSDs.",
#  """
# make_claim_extraction_query(text)
# # %%
# """[
#     {
#         "claim": "SSDs offer a good compromise among performance, capacity, and cost, suggesting that while they may be more expensive, their performance benefits could justify the cost.",
#         "CorpusId": "208963067"
#     },
#     {
#         "claim": "Hard drives are significantly slower than SSDs, which could imply that the higher cost of SSDs is offset by their superior speed.",
#         "CorpusId": "250413695"
#     },
#     {
#         "claim": "The use of high-end SSDs as regular disk storage indicates that SSDs are being adopted despite their cost.",
#         "CorpusId": "17794134"
#     },
#     {
#         "claim": "Hard disks are the most popular secondary storage and are slow, which could be a factor in their lower cost compared to SSDs.",
#         "CorpusId": "118134702"
#     }
# ]"""
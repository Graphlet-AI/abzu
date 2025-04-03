import os

import openai
from langchain.chains import LLMChain
from langchain.docstore.document import Document
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.llms import OpenAI
from langchain_community.vectorstores import FAISS

# Make sure to set your OpenAI API key:
os.environ["OPENAI_API_KEY"] = "sk-proj-"
openai.api_key = "sk-proj-"

spam_prompt_template = """
You are a news headline spam classifier. 
Given the headline below, you must label it as "SPAM" or "NOT SPAM".

Headline: "{headline}"

Classification:
"""

spam_prompt = PromptTemplate(
    input_variables=["headline"],
    template=spam_prompt_template,
)

spam_llm = OpenAI(temperature=0)

spam_chain = LLMChain(llm=spam_llm, prompt=spam_prompt)


def is_spam(headline: str) -> bool:
    """Use the spam_chain to classify each headline."""
    classification = spam_chain.run(headline=headline).strip().upper()
    return classification == "SPAM"


raw_headlines = [
    "Breaking: New vaccine shows 90% effectiveness in latest trial",
    "Sports update: Local team wins championship final!",
    "??? THIS WILL MAKE YOU RICH IN 2 DAYS !!!",
    "Weather alert: Heavy rains predicted all week",
    "New vaccine proves to reduce transmission rates significantly",
    "Expert says stock market on the rise",
    "Buy this amazing product now - offer ends soon!",
    "Local sports team clinches trophy after a thrilling match",
    "Scientists discover new species in the Amazon rainforest",
    "BREAKING NEWS: Vaccine success rate climbs",
]

# Filter out spam
filtered_headlines = []
for headline in raw_headlines:
    if not is_spam(headline):
        filtered_headlines.append(headline)

print("Filtered Headlines:\n", filtered_headlines)


embedding_model = OpenAIEmbeddings()

# Convert each headline into a Document for LangChain
documents = [Document(page_content=headline) for headline in filtered_headlines]

# Create the FAISS vector store from documents
vectorstore = FAISS.from_documents(documents, embedding_model)

from typing import Any, Dict, List


def cluster_headlines(vectorstore, headlines: List[str], threshold: float = 0.8):
    """
    Groups headlines by similarity. Returns a list of clusters,
    where each cluster is a list of headlines considered 'similar'.
    'threshold' is the dot-product similarity threshold.
    """
    clusters = []

    for headline in headlines:
        # Search for the most similar doc among already accepted "representative" docs
        # We'll define the "representative" doc as the first item in each cluster for simplicity
        if not clusters:
            clusters.append([headline])
            continue

        # Compute embedding for current headline
        embedding = embedding_model.embed_query(headline)

        # We’ll keep track of the highest similarity we find among the representative headlines
        best_cluster_index = None
        best_similarity = -1

        for i, cluster in enumerate(clusters):
            rep_headline = cluster[0]  # using the first headline in each cluster as representative
            rep_embedding = embedding_model.embed_query(rep_headline)

            # Dot product or cosine similarity can be used.
            # Using the built-in FAISS store for direct dot-product might be simpler,
            # but let's do a manual dot product as an example:

            sim = sum(a * b for a, b in zip(embedding, rep_embedding))

            if sim > best_similarity:
                best_similarity = sim
                best_cluster_index = i

        # We'll do a simplified approach to interpret "similarity" as higher => more similar
        # Typically you'd want to use cosine similarity and compare to a threshold.
        # For demonstration, let's assume a dot-product threshold or something similar.

        # Example check:
        if best_similarity > threshold:
            # Add to existing cluster
            clusters[best_cluster_index].append(headline)
        else:
            # Create a new cluster
            clusters.append([headline])

    return clusters


clusters = cluster_headlines(vectorstore, filtered_headlines, threshold=0.8)

summary_prompt_template = """
You are an AI assistant that summarizes news headlines. 
Given the following list of related headlines, provide a single short summary:

Headlines:
{headlines}
Summary:
"""

summary_prompt = PromptTemplate(
    input_variables=["headlines"],
    template=summary_prompt_template,
)

summary_chain = LLMChain(llm=OpenAI(temperature=0), prompt=summary_prompt)

unique_summaries = []
for cluster in clusters:
    cluster_text = "\n".join(cluster)
    summary = summary_chain.run(headlines=cluster_text)
    unique_summaries.append(summary.strip())

print("\nSummaries of each cluster:")
for i, summ in enumerate(unique_summaries, 1):
    print(f"{i}. {summ}")

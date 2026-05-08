from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from duckduckgo_search import DDGS
from bs4 import BeautifulSoup

import requests

# ===========================g76f7f===========
# LLM
# ======================================
jj
llm = ChatOpenAI(
    base_url="http://43.134.132.230:11434/v1",
    api_key="dummy",
    model="qwen2.5:3b",
    temperature=0.3,
)

# ======================================
# Embedding Model
# ======================================

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://43.134.132.230:11434"
)

# ======================================
# Input Topic
# ======================================

topic = input("Topik: ")

# ======================================
# Search Web
# ======================================

print("\nMencari artikel...\n")

results = DDGS().text(
    topic,
    max_results=3
)

documents = []

for r in results:

    try:
        url = r["href"]

        print(f"Load: {url}")

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        soup = BeautifulSoup(
            response.text,
            "lxml"
        )

        text = soup.get_text(
            " ",
            strip=True
        )

        documents.append(text)

    except Exception as e:
        print(e)

# ======================================
# Split Documents
# ======================================

print("\nChunking document...\n")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = splitter.create_documents(
    documents
)

print(f"Total chunks: {len(chunks)}")

# ======================================
# Vector Store
# ======================================

print("\nCreating vector store...\n")

vectorstore = FAISS.from_documents(
    chunks,
    embeddings
)

# ======================================
# Retrieval
# ======================================

retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 5
    }
)

retrieved_docs = retriever.invoke(topic)

context = "\n\n".join(
    doc.page_content
    for doc in retrieved_docs
)

# ======================================
# Final Prompt
# ======================================

prompt = f"""
Jelaskan topik berikut secara jelas dan terstruktur.

TOPIK:
{topic}

KONTEKS:
{context}

Buat penjelasan:
- mudah dipahami
- ringkas
- terstruktur
- fokus pada inti pembahasan
"""

print("\nQwen sedang membuat jawaban...\n")

response = llm.invoke(prompt)

print("\n===== HASIL =====\n")

print(response.content)
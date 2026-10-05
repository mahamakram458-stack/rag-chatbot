import os
import time
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

load_dotenv()
emb = SentenceTransformer("all-MiniLM-L6-v2")
col = chromadb.PersistentClient(path="db").get_or_create_collection("docs")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL")


def gen(**kwargs):
    for attempt in range(5):
        try:
            return client.models.generate_content(**kwargs)
        except Exception as e:
            if "429" in str(e) or "503" in str(e):
                wait = 20 * (attempt + 1)
                print(f"API busy, {wait}s wait...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("API limit: retries finished")


def chunk(text, size=500, overlap=100):
    step = size - overlap
    return [text[i:i + size] for i in range(0, len(text), step) if text[i:i + size].strip()]


def ingest(pdf_path):
    name = Path(pdf_path).name
    ids, docs, metas = [], [], []
    for p, page in enumerate(PdfReader(pdf_path).pages, 1):
        for i, c in enumerate(chunk(page.extract_text() or "")):
            ids.append(f"{name}-{p}-{i}")
            docs.append(c)
            metas.append({"file": name, "page": p})
    if docs:
        col.upsert(ids=ids, documents=docs, metadatas=metas,
                   embeddings=emb.encode(docs).tolist())
    print(f"Ingested {len(docs)} chunks from {name}")


def to_english(q):
    r = gen(
        model=MODEL,
        contents=(
            "Rewrite this question as one complete, natural English question. "
            "Keep technical terms. Output only the question:\n" + q
        ),
    )
    return r.text.strip() or q


def ask(question, k=8):
    search_q = to_english(question)
    print("SEARCH:", search_q)
    hits = col.query(query_embeddings=emb.encode([search_q]).tolist(), n_results=k)
    context = "\n\n".join(hits["documents"][0])
    r = gen(
        model=MODEL,
        contents=f"Context:\n{context}\n\nQuestion: {question}",
        config={
            "system_instruction": (
                "Answer ONLY from the context. Reply in the same language "
                "as the question. If the answer is not in the context, "
                "reply exactly: I could not find this."
            ),
            "temperature": 0,
        },
    )
    return r.text, hits["metadatas"][0]


if __name__ == "__main__":
    ingest("notes.pdf")
    ingest("Day1_Python_Basics.pdf")
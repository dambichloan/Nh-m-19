"""Nạp file chính sách vào Chroma. Chạy: python -m app.ingest"""
import glob
import os
import re

import chromadb
from dotenv import load_dotenv

load_dotenv()

POLICY_DIR = "data/policies"
DB_DIR = "data/chroma"
COLLECTION = "policies"
EMBED_MODEL = "models/gemini-embedding-001"
MAX_CHARS = 1500   # khoảng 400 token
OVERLAP = 200      # khoảng 50 token


def get_embedder():
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    return GoogleGenerativeAIEmbeddings(model=EMBED_MODEL, google_api_key=key)


def chunk_file(text: str) -> list[str]:
    """Tách theo tiêu đề '## ', mục nào quá dài thì cắt thêm có overlap."""
    lines = text.strip().split("\n")
    title = lines[0].lstrip("# ").strip() if lines[0].startswith("# ") else ""
    body = "\n".join(lines[1:]) if title else text
    sections = [s.strip() for s in re.split(r"\n(?=## )", body) if s.strip()]

    chunks = []
    for sec in sections:
        start = 0
        while True:
            piece = sec[start:start + MAX_CHARS]
            chunks.append(f"{title}\n{piece}" if title else piece)
            if start + MAX_CHARS >= len(sec):
                break
            start += MAX_CHARS - OVERLAP
    return chunks


def main():
    embedder = get_embedder()
    client = chromadb.PersistentClient(path=DB_DIR)
    try:
        client.delete_collection(COLLECTION)   # nạp lại từ đầu cho sạch
    except Exception:
        pass
    col = client.create_collection(COLLECTION)

    total = 0
    for path in sorted(glob.glob(f"{POLICY_DIR}/*.md")):
        name = os.path.basename(path)
        if name.lower() == "readme.md":
            continue
        with open(path, encoding="utf-8") as f:
            chunks = chunk_file(f.read())
        ids = [f"{name}#{i}" for i in range(1, len(chunks) + 1)]
        col.add(
            ids=ids,
            documents=chunks,
            embeddings=embedder.embed_documents(chunks),
            metadatas=[{"source": i} for i in ids],
        )
        total += len(chunks)
        print(f"{name}: {len(chunks)} đoạn")
    print(f"Xong. Tổng {total} đoạn.")


if __name__ == "__main__":
    main()
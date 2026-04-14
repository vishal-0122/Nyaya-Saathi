import json
from pathlib import Path
from app.core.rag.embedding import embed_text
from app.db.chroma.client import get_collection, reset_collection


def main():
    # 🔁 Reset collection (clean start)
    collection = reset_collection()

    # 📂 Load JSON file
    json_path = Path("data/raw/legal_data.json")

    if not json_path.exists():
        raise FileNotFoundError(f"{json_path} not found!")

    with open(json_path, "r", encoding="utf-8") as f:
        legal_data = json.load(f)

    ids, documents, embeddings, metadatas = [], [], [], []
    seen_ids = set()

    for entry in legal_data:
        section_id = entry.get("section")

        # 🛑 Skip duplicates or invalid entries
        if not section_id or section_id in seen_ids:
            continue

        seen_ids.add(section_id)

        # 🧠 Better structured text for embeddings
        text = f"""
        Section: {entry.get('section')}
        Title: {entry.get('title')}
        Description: {entry.get('description')}
        Category: {entry.get('category')}
        """

        try:
            embedding = embed_text(text)
        except Exception as e:
            print(f"Embedding failed for {section_id}: {e}")
            continue

        ids.append(section_id)
        documents.append(entry["description"])
        embeddings.append(embedding)
        metadatas.append({
            "section": entry["section"],
            "title": entry["title"],
            "category": entry["category"],
            "description": entry["description"],  # 🔥 ADD THIS
        })

    # 🚀 Batch insert
    if ids:
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    print(f"✅ Inserted {len(ids)} legal documents into ChromaDB.")


if __name__ == "__main__":
    main()
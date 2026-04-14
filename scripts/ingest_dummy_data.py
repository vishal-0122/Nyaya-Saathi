
from app.core.rag.embedding import embed_text
from app.db.chroma.client import get_collection

def main():
	legal_texts = [
    "IPC Section 279: Rash driving or riding on a public way is punishable.",
    "IPC Section 304A: Causing death by negligence can lead to imprisonment.",
    "Article 21: Protection of life and personal liberty.",
    "IPC Section 354: Assault or criminal force to woman with intent to outrage modesty.",
    "IPC Section 420: Cheating and dishonestly inducing delivery of property."
	]
	collection = get_collection()
	for i, text in enumerate(legal_texts):
		embedding = embed_text(text)
		# Use a unique id for each document
		doc_id = f"doc_{i+1}"
		collection.add(
			ids=[doc_id],
			documents=[text],
			embeddings=[embedding]
		)
	print("Inserted dummy legal documents into ChromaDB.")

if __name__ == "__main__":
	main()

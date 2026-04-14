import chromadb

client = chromadb.PersistentClient(path="./data/chroma")

collection = client.get_collection("legal_docs")

# Print all documents
results = collection.get()

print("Documents:")
print(results["documents"])

print("\nMetadata:")
print(results["metadatas"])


import chromadb

# Initialize persistent ChromaDB client
_client = chromadb.PersistentClient(path="./data/chroma")


def get_collection():
	"""
	Returns the 'legal_docs' collection, creating it if it doesn't exist.
	"""
	return _client.get_or_create_collection("legal_docs")

def reset_collection():
	"""
	Deletes the 'legal_docs' collection if it exists and recreates it as empty.
	"""
	try:
		_client.delete_collection("legal_docs")
	except Exception as e:
		print(f"Error occurred while deleting collection: {e}")
	
	collection = _client.create_collection("legal_docs")
	return collection
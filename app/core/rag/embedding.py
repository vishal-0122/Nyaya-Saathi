
import os
import requests

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "nomic-embed-text")
OLLAMA_EMBED_URLS = [
	os.getenv("OLLAMA_EMBED_URL"),
	"http://ollama:11434/api/embeddings",
	"http://host.docker.internal:11434/api/embeddings",
	"http://localhost:11434/api/embeddings",
]

def embed_text(text: str):
	"""
	Generate an embedding vector for the given text using Ollama's nomic-embed-text model.
	"""
	payload = {
		"model": OLLAMA_MODEL,
		"prompt": text
	}

	last_error = None
	seen = set()
	for url in OLLAMA_EMBED_URLS:
		if not url or url in seen:
			continue
		seen.add(url)
		try:
			response = requests.post(url, json=payload, timeout=8)
			response.raise_for_status()
			data = response.json()
			return data["embedding"]
		except Exception as exc:
			last_error = exc

	raise RuntimeError(f"Failed to generate embeddings from configured Ollama endpoints: {last_error}")

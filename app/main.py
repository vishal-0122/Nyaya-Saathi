
import logging
logging.basicConfig(level=logging.INFO)

# Suppress LangSmith client connection warnings (SSL issues are environmental)
logging.getLogger("langsmith.client").setLevel(logging.ERROR)
logging.getLogger("langsmith").setLevel(logging.ERROR)

from fastapi import FastAPI
from dotenv import load_dotenv
from app.core.observability.langsmith_config import configure_langsmith

load_dotenv()
configure_langsmith()

app = FastAPI()

# Import router
from app.api.routes import query as query_router
app.include_router(query_router.router)

@app.get("/health")
async def health():
	return {"status": "ok"}

if __name__ == "__main__":
	import uvicorn
	uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
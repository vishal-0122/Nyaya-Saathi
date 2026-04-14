from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import socket
import logging


logger = logging.getLogger(__name__)


def _with_ipv4_hostaddr(db_url: str) -> str:
	"""Resolve DB host to IPv4 and inject hostaddr for psycopg2 in Docker-friendly environments."""
	if not db_url:
		return db_url

	try:
		url = make_url(db_url)
	except Exception:
		return db_url

	if not url.drivername.startswith("postgresql") or not url.host:
		return db_url

	# Supabase pooler endpoints should be used as-is; forcing hostaddr can break auth routing.
	host_lower = url.host.lower()
	if "pooler.supabase.com" in host_lower:
		logger.info("Skipping hostaddr injection for pooler host '%s'", url.host)
		return db_url

	try:
		ipv4_records = socket.getaddrinfo(
			url.host,
			url.port or 5432,
			socket.AF_INET,
			socket.SOCK_STREAM,
		)
		if not ipv4_records:
			return db_url

		hostaddr = ipv4_records[0][4][0]
		query = dict(url.query)
		query.setdefault("hostaddr", hostaddr)
		updated_url = url.set(query=query)
		logger.info("Using IPv4 hostaddr for database host '%s': %s", url.host, hostaddr)
		return str(updated_url)
	except Exception as exc:
		logger.warning("Could not resolve IPv4 for database host '%s': %s", url.host, exc)
		return db_url


def _select_database_url() -> str:
	"""Choose DB URL with Docker-safe fallback support.

	Priority:
	1) DATABASE_URL_DOCKER (recommended for containers; set this to Supabase pooler URL)
	2) SUPABASE_POOLER_URL
	3) DATABASE_URL (existing default)
	"""
	candidates = [
		("DATABASE_URL_DOCKER", os.getenv("DATABASE_URL_DOCKER")),
		("SUPABASE_POOLER_URL", os.getenv("SUPABASE_POOLER_URL")),
		("DATABASE_URL", os.getenv("DATABASE_URL")),
	]

	for env_name, raw_url in candidates:
		if not raw_url:
			continue
		selected = _with_ipv4_hostaddr(raw_url)
		logger.info("Using %s for database connection", env_name)
		return selected

	raise ValueError(
		"No database URL found. Set DATABASE_URL or DATABASE_URL_DOCKER (preferred for Docker)."
	)


# Example: postgresql://user:password@localhost/dbname
DATABASE_URL = _select_database_url()

if not DATABASE_URL:
	raise ValueError("DATABASE_URL is not set. Please configure it in environment variables.")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"sslmode": "require"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

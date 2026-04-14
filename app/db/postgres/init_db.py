# Import models so that Base.metadata.create_all sees them
from app.db.postgres.connection import Base, engine
from app.db.postgres import models

def init_db():
	Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
	init_db()
	print("Database tables created.")

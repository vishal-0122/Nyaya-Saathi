import sys
import os
import random
from faker import Faker
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.db.postgres.connection import SessionLocal
from app.db.postgres.models import Lawyer

def seed_lawyers():
    fake = Faker()
    cities = [
        "Delhi", "Mumbai", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
        "Chandigarh", "Bhopal", "Indore", "Patna", "Surat"
    ]
    practice_areas = [
        "Criminal Law", "Civil Law", "Family Law", "Corporate Law", "Cyber Law", "Administrative Law", "Tax Law"
    ]
    first_names = [
        "Amit", "Priya", "Rohit", "Sneha", "Vikram", "Anjali", "Suresh", "Neha", "Rajesh", "Sunita",
        "Deepak", "Kavita", "Manish", "Pooja", "Sanjay", "Meena", "Arun", "Ritu", "Nitin", "Shalini", "Vishal"
    ]
    last_names = [
        "Sharma", "Verma", "Mehra", "Rao", "Singh", "Nair", "Patel", "Dangiwala", "Gupta", "Jain", "Kumar",
        "Chopra", "Joshi", "Reddy", "Das", "Bose", "Mishra", "Yadav", "Choudhary", "Saxena", "Kapoor"
    ]

    db = SessionLocal()
    try:
        # Optional: Clear table before insert to avoid duplicates
        from sqlalchemy import text
        db.execute(text('DELETE FROM lawyers'))
        db.commit()

        lawyers = []
        for _ in range(300):
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            city = random.choice(cities)
            practice_area = random.choice(practice_areas)
            contact = fake.msisdn()[:10]  # 10-digit random number
            lawyers.append(Lawyer(name=name, city=city, practice_area=practice_area, contact=contact))

        db.add_all(lawyers)
        db.commit()
        print("Inserted 300 lawyers successfully")
    finally:
        db.close()

if __name__ == "__main__":
    seed_lawyers()

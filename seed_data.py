from app import app, db, User, Item
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def seed():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Create Admin
        admin = User(
            name="Admin User",
            email="admin@example.com",
            password=generate_password_hash("admin123", method='pbkdf2:sha256'),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        
        # Create Found Items with specific user-provided images
        f1 = Item(
            title="Black Leather Wallet",
            description="Found a premium black leather wallet with a student ID for 'Alex'. Mint condition.",
            location="Library Entrance",
            date=datetime.utcnow() - timedelta(days=1),
            contact="555-0101",
            type="found",
            reporter_name="Security Desk",
            image="https://m.media-amazon.com/images/I/81TaMxHjJdL._AC_.jpg"
        )
        
        f2 = Item(
            title="Silver iPhone 13 Pro",
            description="Silver iPhone with a clear case. Screen is intact, found on a wooden bench.",
            location="Main Courtyard",
            date=datetime.utcnow() - timedelta(hours=5),
            contact="555-0202",
            type="found",
            reporter_name="Jane Doe",
            image="https://smarttek.pe/wp-content/uploads/2022/01/13-PRO-MAX-SILVER11.jpg"
        )
        
        f3 = Item(
            title="Tech Backpack (Navy)",
            description="Durable navy blue backpack with a laptop charger inside. Left in the cafeteria.",
            location="Cafeteria",
            date=datetime.utcnow() - timedelta(days=2),
            contact="Admin Desk",
            type="found",
            reporter_name="Office Staff",
            category="admin_desk",
            image="https://i5.walmartimages.com/seo/2023-Easton-Walk-Off-NX-Backpack-Navy-Any_1e13c084-24a4-4e16-8246-3bb782dd628f.ae3f90d7d4322e0f3e2a7c48b03f8634.jpeg"
        )
        
        db.session.add_all([f1, f2, f3])
        db.session.commit()
        print("Database seeded with Admin and Premium Sample Items!")

if __name__ == "__main__":
    seed()

import random
from datetime import datetime, timedelta
from database import SessionLocal, engine, Base
from models import Product, Order, User
from auth import hash_password

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
db = SessionLocal()

data = [
    ("Wireless Earbuds", 59, 30, 40),
    ("Smart Watch", 129, 70, 25),
    ("Phone Case", 15, 4, 120),
    ("Laptop Stand", 45, 20, 8),
    ("USB-C Cable", 12, 3, 200),
    ("Mechanical Keyboard", 99, 55, 18),
    ("Gaming Mouse", 49, 22, 35),
    ("Webcam HD", 69, 35, 5),
    ("Desk Lamp", 39, 16, 60),
    ("Power Bank", 35, 15, 45),
]

products = []
for name, price, cost, stock in data:
    p = Product(name=name, price=price, cost=cost, stock=stock)
    db.add(p)
    products.append(p)
db.commit()

now = datetime.now()
for days_ago in range(60, -1, -1):
    day = now - timedelta(days=days_ago)
    for _ in range(random.randint(4, 10)):
        p = random.choice(products)
        # مبيعات Smart Watch بتقل في آخر 14 يوم
        if p.name == "Smart Watch" and days_ago < 14 and random.random() < 0.8:
            continue
        qty = random.randint(1, 3)
        db.add(Order(product_id=p.id, quantity=qty, total=qty * p.price, created_at=day))
db.commit()

db.add(User(username="admin", password_hash=hash_password("admin123"), role="admin"))
db.add(User(username="viewer", password_hash=hash_password("viewer123"), role="viewer"))
db.commit()

print("Products:", db.query(Product).count())
print("Orders:", db.query(Order).count())
print("Users:", db.query(User).count())
db.close()
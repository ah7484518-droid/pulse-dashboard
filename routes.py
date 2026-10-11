from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from models import Product, Order
from auth import get_current_user
from insights import build_insights
from summary import build_summary

router = APIRouter(prefix="/api", dependencies=[Depends(get_current_user)])


@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [
        {"id": p.id, "name": p.name, "price": p.price, "cost": p.cost, "stock": p.stock}
        for p in products
    ]


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    since = datetime.now() - timedelta(days=30)
    orders = db.query(Order).filter(Order.created_at >= since).all()
    prices = {p.id: p for p in db.query(Product).all()}
    revenue = sum(o.total for o in orders)
    profit = sum(o.total - o.quantity * prices[o.product_id].cost for o in orders)
    return {
        "revenue_30d": round(revenue, 2),
        "profit_30d": round(profit, 2),
        "orders_30d": len(orders),
        "products": len(prices),
    }


@router.get("/sales-by-day")
def sales_by_day(db: Session = Depends(get_db)):
    since = datetime.now() - timedelta(days=30)
    rows = (
        db.query(func.date(Order.created_at), func.sum(Order.total))
        .filter(Order.created_at >= since)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
        .all()
    )
    return [{"date": str(d), "total": round(t, 2)} for d, t in rows]


@router.get("/insights")
def insights(db: Session = Depends(get_db)):
    summary = {
        "type": "summary",
        "level": "good",
        "title": "Daily summary",
        "message": build_summary(db),
    }
    return [summary] + build_insights(db)
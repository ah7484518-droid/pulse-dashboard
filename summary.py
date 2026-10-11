from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from models import Product, Order


def _revenue_between(db: Session, start, end):
    total = (
        db.query(func.sum(Order.total))
        .filter(Order.created_at >= start, Order.created_at < end)
        .scalar()
    )
    return total or 0


def build_summary(db: Session) -> str:
    now = datetime.now()
    this_week = _revenue_between(db, now - timedelta(days=7), now)
    last_week = _revenue_between(db, now - timedelta(days=14), now - timedelta(days=7))

    if last_week > 0:
        change = (this_week - last_week) / last_week * 100
        if change >= 5:
            trend = f"Revenue is up {change:.0f}% compared with last week"
        elif change <= -5:
            trend = f"Revenue is down {abs(change):.0f}% compared with last week"
        else:
            trend = "Revenue is steady compared with last week"
    else:
        trend = "Not enough data to compare with last week"

    parts = [f"{trend}, at ${this_week:,.0f} over the last 7 days."]

    low = db.query(Product).filter(Product.stock < 10).all()
    if low:
        names = ", ".join(p.name for p in low)
        parts.append(f"{len(low)} product(s) are low on stock: {names}.")
    else:
        parts.append("Stock levels look healthy.")

    top = (
        db.query(Product.name, func.sum(Order.total))
        .join(Order, Order.product_id == Product.id)
        .filter(Order.created_at >= now - timedelta(days=7))
        .group_by(Product.name)
        .order_by(func.sum(Order.total).desc())
        .first()
    )
    if top:
        parts.append(f"Best seller this week: {top[0]}.")

    parts.append("See the cards below for suggested actions.")
    return " ".join(parts)
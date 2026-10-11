from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from models import Product, Order


def build_insights(db: Session):
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    month_ago = now - timedelta(days=30)

    products = db.query(Product).all()
    cards = []

    # مبيعات كل منتج في آخر 14 يوم (للتنبؤ بنفاد المخزون)
    sold_14d = dict(
        db.query(Order.product_id, func.sum(Order.quantity))
        .filter(Order.created_at >= two_weeks_ago)
        .group_by(Order.product_id)
        .all()
    )

    # 1) مخزون قليل
    for p in products:
        per_day = (sold_14d.get(p.id, 0) or 0) / 14
        if p.stock < 10:
            if per_day > 0:
                days_left = max(1, int(p.stock / per_day))
                msg = f"{p.name} has {p.stock} units left, about {days_left} days of sales. Reorder soon."
            else:
                msg = f"{p.name} has only {p.stock} units left. Consider reordering."
            cards.append({"type": "stock", "level": "high", "title": "Low stock", "message": msg})

    # 2) مبيعات بتقع (آخر 7 أيام مقابل الـ 7 اللي قبلها)
    def sold_between(start, end):
        return dict(
            db.query(Order.product_id, func.sum(Order.quantity))
            .filter(Order.created_at >= start, Order.created_at < end)
            .group_by(Order.product_id)
            .all()
        )

    this_week = sold_between(week_ago, now)
    last_week = sold_between(two_weeks_ago, week_ago)
    for p in products:
        a = last_week.get(p.id, 0) or 0
        b = this_week.get(p.id, 0) or 0
        if a >= 5 and b < a * 0.6:
            drop = int((1 - b / a) * 100)
            cards.append({
                "type": "drop", "level": "medium", "title": "Sales dropping",
                "message": f"{p.name} sales fell {drop}% versus last week. Consider a promotion or a price check.",
            })

    # 3) أحسن منتج في آخر 7 أيام
    best = (
        db.query(Product.name, func.sum(Order.total).label("rev"))
        .join(Order, Order.product_id == Product.id)
        .filter(Order.created_at >= week_ago)
        .group_by(Product.name)
        .order_by(func.sum(Order.total).desc())
        .first()
    )
    if best:
        cards.append({
            "type": "best", "level": "good", "title": "Top product this week",
            "message": f"{best[0]} led sales with ${round(best[1]):,} in revenue.",
        })

    # 4) منتج هامش ربحه عالي ومبيعاته قليلة (فرصة)
    sold_30d = dict(
        db.query(Order.product_id, func.sum(Order.quantity))
        .filter(Order.created_at >= month_ago)
        .group_by(Order.product_id)
        .all()
    )
    opportunities = [
        p for p in products
        if (p.price - p.cost) / p.price > 0.55 and (sold_30d.get(p.id, 0) or 0) < 20
    ]
    if opportunities:
        o = opportunities[0]
        m = int((o.price - o.cost) / o.price * 100)
        cards.append({
            "type": "opportunity", "level": "good", "title": "Opportunity",
            "message": f"{o.name} has a {m}% margin but low sales. Promoting it could lift profit.",
        })

    return cards
from database.db import connect

def today_summary():
    with connect() as conn:
        row = conn.execute("""
            SELECT COALESCE(SUM(total),0) revenue, COALESCE(SUM(quantity),0) units,
                   COUNT(*) transactions
            FROM sales WHERE date(created_at,'localtime')=date('now','localtime')
        """).fetchone()
        profit_row = conn.execute("""
            SELECT COALESCE(SUM(s.quantity * (s.unit_price - COALESCE(p.cost_price, s.unit_price * 0.75))), 0) profit
            FROM sales s JOIN products p ON p.id=s.product_id
            WHERE date(s.created_at,'localtime')=date('now','localtime')
        """).fetchone()
        top = conn.execute("""
            SELECT p.name,SUM(s.quantity) quantity,p.unit,SUM(s.total) revenue
            FROM sales s JOIN products p ON p.id=s.product_id
            WHERE date(s.created_at,'localtime')=date('now','localtime')
            GROUP BY p.id ORDER BY quantity DESC LIMIT 1
        """).fetchone()
    return {
        "revenue": float(row["revenue"]),
        "units": float(row["units"]),
        "transactions": int(row["transactions"]),
        "profit": float(profit_row["profit"]) if profit_row else 0.0,
        "top_product": dict(top) if top else None
    }

def list_sales(limit=50, offset=0, start_date=None, end_date=None, product_name=None):
    query = """
        SELECT s.id, p.name as product_name, p.category, s.quantity, p.unit, s.unit_price, s.total, s.created_at
        FROM sales s
        JOIN products p ON p.id = s.product_id
        WHERE 1=1
    """
    params = []
    if start_date:
        query += " AND date(s.created_at, 'localtime') >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date(s.created_at, 'localtime') <= ?"
        params.append(end_date)
    if product_name:
        query += " AND p.name LIKE ? COLLATE NOCASE"
        params.append(f"%{product_name}%")
    query += " ORDER BY s.id DESC LIMIT ? OFFSET ?"
    params.extend([int(limit), int(offset)])

    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
        count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    return {"sales": [dict(r) for r in rows], "total_count": count}

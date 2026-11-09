from database.db import connect

def low_stock_items():
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT name,quantity,unit,low_stock_threshold FROM products WHERE quantity <= low_stock_threshold ORDER BY quantity"
        )]

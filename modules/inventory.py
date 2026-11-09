from database.db import connect

def list_products():
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM products ORDER BY name")]

def find_product(name):
    name = (name or "").strip()
    if not name:
        return None
    with connect() as conn:
        row = conn.execute("SELECT * FROM products WHERE name=? COLLATE NOCASE", (name,)).fetchone()
        if row:
            return dict(row)
        row = conn.execute("SELECT * FROM products WHERE name LIKE ? COLLATE NOCASE ORDER BY LENGTH(name) LIMIT 1", (f"%{name}%",)).fetchone()
        return dict(row) if row else None

def create_product(name, quantity=0, unit="pcs", price=0, low_stock_threshold=5, category="General", cost_price=0):
    name = str(name or "").strip()
    unit = str(unit or "pcs").strip()[:12]
    category = str(category or "General").strip()[:40]
    try:
        quantity, price, low_stock_threshold, cost_price = float(quantity), float(price), float(low_stock_threshold), float(cost_price)
    except (TypeError, ValueError):
        raise ValueError("Quantity, price and low-stock threshold must be numbers.")
    if not name or len(name) > 80:
        raise ValueError("Enter a product name (maximum 80 characters).")
    if min(quantity, price, low_stock_threshold, cost_price) < 0:
        raise ValueError("Numbers cannot be negative.")
    with connect() as conn:
        try:
            cur = conn.execute("""INSERT INTO products(name, category, quantity, unit, price, cost_price, low_stock_threshold)
                                  VALUES(?,?,?,?,?,?,?)""",
                               (name, category, quantity, unit, price, cost_price, low_stock_threshold))
        except Exception as exc:
            if "UNIQUE" in str(exc).upper():
                raise ValueError("That product already exists.")
            raise
        row = conn.execute("SELECT * FROM products WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)

def update_product(product_id, name, category, quantity, unit, price, cost_price, low_stock_threshold):
    with connect() as conn:
        conn.execute("""
            UPDATE products
            SET name=?, category=?, quantity=?, unit=?, price=?, cost_price=?, low_stock_threshold=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (name, category, float(quantity), unit, float(price), float(cost_price), float(low_stock_threshold), int(product_id)))
        row = conn.execute("SELECT * FROM products WHERE id=?", (int(product_id),)).fetchone()
        return dict(row) if row else None

def delete_product(product_id):
    with connect() as conn:
        conn.execute("DELETE FROM products WHERE id=?", (int(product_id),))
        return True

def change_stock(product_name, amount, movement_type="stock_in", note="AI assistant"):
    amount = float(amount)
    if amount <= 0:
        raise ValueError("Quantity must be greater than zero.")
    with connect() as conn:
        product = conn.execute("SELECT * FROM products WHERE name=? COLLATE NOCASE", (product_name,)).fetchone()
        if not product:
            raise ValueError(f"I couldn't find {product_name}. Add it in the product catalogue first.")
        new_qty = product["quantity"] + amount if movement_type == "stock_in" else product["quantity"] - amount
        if new_qty < 0:
            raise ValueError(f"Not enough {product_name} in stock. Available: {product['quantity']} {product['unit']}.")
        conn.execute("UPDATE products SET quantity=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (new_qty, product["id"]))
        conn.execute("INSERT INTO stock_movements(product_id,movement_type,quantity,note) VALUES(?,?,?,?)",
                     (product["id"], movement_type, amount, note))
        if movement_type == "sale":
            total = amount * product["price"]
            conn.execute("INSERT INTO sales(product_id,quantity,unit_price,total) VALUES(?,?,?,?)",
                         (product["id"], amount, product["price"], total))
        return {"name": product["name"], "quantity": new_qty, "unit": product["unit"],
                "price": product["price"], "sale_total": amount * product["price"] if movement_type == "sale" else None}

import csv
import io
import re
from pathlib import Path
from database.db import connect
from gnani.prisma import transcribe_audio

def extract_from_csv(file_bytes_or_text):
    if isinstance(file_bytes_or_text, bytes):
        text = file_bytes_or_text.decode("utf-8", errors="ignore")
    else:
        text = str(file_bytes_or_text)

    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader if r and any(c.strip() for c in r)]
    if not rows:
        return []

    # Detect header row
    header = [c.strip().lower() for c in rows[0]]
    col_map = {}
    for idx, col in enumerate(header):
        if any(k in col for k in ["name", "product", "item", "description"]):
            col_map["name"] = idx
        elif any(k in col for k in ["category", "cat", "dept", "group"]):
            col_map["category"] = idx
        elif any(k in col for k in ["qty", "quantity", "stock", "count", "units"]):
            col_map["quantity"] = idx
        elif any(k in col for k in ["unit", "uom", "measure"]):
            col_map["unit"] = idx
        elif any(k in col for k in ["price", "rate", "mrp", "selling"]):
            col_map["price"] = idx
        elif any(k in col for k in ["cost", "purchase", "buying"]):
            col_map["cost_price"] = idx
        elif any(k in col for k in ["threshold", "min", "reorder", "alert"]):
            col_map["low_stock_threshold"] = idx

    start_idx = 1 if "name" in col_map else 0
    items = []
    for r in rows[start_idx:]:
        if len(r) == 0:
            continue
        try:
            name = r[col_map.get("name", 0)].strip() if len(r) > col_map.get("name", 0) else f"Product {len(items)+1}"
            if not name:
                continue

            category = r[col_map["category"]].strip() if "category" in col_map and len(r) > col_map["category"] else "General"

            raw_qty = r[col_map["quantity"]].strip() if "quantity" in col_map and len(r) > col_map["quantity"] else "10"
            qty_match = re.search(r"[-+]?\d*\.?\d+", raw_qty)
            quantity = float(qty_match.group(0)) if qty_match else 0.0

            unit = r[col_map["unit"]].strip() if "unit" in col_map and len(r) > col_map["unit"] else "pcs"

            raw_price = r[col_map["price"]].strip() if "price" in col_map and len(r) > col_map["price"] else "0"
            price_match = re.search(r"[-+]?\d*\.?\d+", raw_price)
            price = float(price_match.group(0)) if price_match else 0.0

            raw_cost = r[col_map["cost_price"]].strip() if "cost_price" in col_map and len(r) > col_map["cost_price"] else "0"
            cost_match = re.search(r"[-+]?\d*\.?\d+", raw_cost)
            cost_price = float(cost_match.group(0)) if cost_match else round(price * 0.8, 2)

            threshold = 5.0
            if "low_stock_threshold" in col_map and len(r) > col_map["low_stock_threshold"]:
                thresh_match = re.search(r"[-+]?\d*\.?\d+", r[col_map["low_stock_threshold"]])
                if thresh_match:
                    threshold = float(thresh_match.group(0))

            items.append({
                "name": name,
                "category": category or "General",
                "quantity": quantity,
                "unit": unit or "pcs",
                "price": price,
                "cost_price": cost_price,
                "low_stock_threshold": threshold
            })
        except Exception:
            continue
    return items

def extract_from_excel(file_bytes_or_path):
    try:
        import openpyxl
        if isinstance(file_bytes_or_path, (str, Path)):
            wb = openpyxl.load_workbook(file_bytes_or_path, data_only=True)
        else:
            wb = openpyxl.load_workbook(io.BytesIO(file_bytes_or_path), data_only=True)
        sheet = wb.active
        rows = []
        for row in sheet.iter_rows(values_only=True):
            if any(cell is not None for cell in row):
                rows.append([str(c or "").strip() for c in row])

        if not rows:
            return []

        # Convert to CSV format and use column mapper
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerows(rows)
        return extract_from_csv(csv_buffer.getvalue())
    except Exception as exc:
        raise RuntimeError(f"Excel parsing error: {exc}")

def extract_from_pdf(file_bytes_or_path):
    try:
        from pypdf import PdfReader
        if isinstance(file_bytes_or_path, (str, Path)):
            reader = PdfReader(str(file_bytes_or_path))
        else:
            reader = PdfReader(io.BytesIO(file_bytes_or_path))

        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

        items = []
        # Pattern: [Item Name] [Quantity] [Unit] [Price] or similar bill line items
        lines = [line.strip() for line in full_text.splitlines() if line.strip()]
        for line in lines:
            # Try to match typical Kirana invoices / inventory tables
            # e.g.: "1. Rice 25 kg 58.00" or "Sugar 10 kg Rs 45" or "Soap - 20 pcs - 35"
            match = re.search(
                r"(?:^\d+[\.\)]\s*)?([A-Za-z\s]+?)\s+(\d+(?:\.\d+)?)\s*(kg|pcs|pkt|l|litres|grams|gm|box)?\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)?",
                line,
                re.IGNORECASE
            )
            if match:
                name = match.group(1).strip()
                qty = float(match.group(2))
                unit = match.group(3) or "pcs"
                price = float(match.group(4)) if match.group(4) else 0.0
                if len(name) > 2 and not name.lower() in ["total", "subtotal", "date", "invoice", "gst", "cgst", "sgst"]:
                    items.append({
                        "name": name.title(),
                        "category": "General",
                        "quantity": qty,
                        "unit": unit.lower(),
                        "price": price,
                        "cost_price": round(price * 0.8, 2),
                        "low_stock_threshold": 5.0
                    })
        return items, full_text
    except Exception as exc:
        raise RuntimeError(f"PDF parsing error: {exc}")

def extract_from_image(file_bytes_or_path):
    # Try pytesseract OCR if system has tesseract; otherwise provide clear structured extract
    try:
        from PIL import Image
        if isinstance(file_bytes_or_path, (str, Path)):
            img = Image.open(str(file_bytes_or_path))
        else:
            img = Image.open(io.BytesIO(file_bytes_or_path))

        ocr_text = ""
        try:
            import pytesseract
            ocr_text = pytesseract.image_to_string(img)
        except Exception:
            # Tesseract binary not installed on OS, return fallback note
            ocr_text = "Image loaded successfully. Please review or manually add scanned items."

        items = []
        if ocr_text:
            lines = [l.strip() for l in ocr_text.splitlines() if l.strip()]
            for line in lines:
                m = re.search(r"([A-Za-z\s]+?)\s+(\d+)\s*(kg|pcs|pkt|l)?\s*(\d+)?", line, re.IGNORECASE)
                if m:
                    name = m.group(1).strip()
                    if len(name) > 2:
                        items.append({
                            "name": name.title(),
                            "category": "General",
                            "quantity": float(m.group(2)),
                            "unit": (m.group(3) or "pcs").lower(),
                            "price": float(m.group(4)) if m.group(4) else 50.0,
                            "cost_price": round(float(m.group(4) or 50.0) * 0.8, 2),
                            "low_stock_threshold": 5.0
                        })
        return items, ocr_text
    except Exception as exc:
        raise RuntimeError(f"Image processing error: {exc}")

def save_confirmed_items(items):
    saved_count = 0
    with connect() as conn:
        for it in items:
            name = str(it.get("name", "")).strip()
            if not name:
                continue
            cat = str(it.get("category", "General")).strip()
            qty = max(0.0, float(it.get("quantity", 0)))
            unit = str(it.get("unit", "pcs")).strip()
            price = max(0.0, float(it.get("price", 0)))
            cost = max(0.0, float(it.get("cost_price", round(price * 0.8, 2))))
            thresh = max(1.0, float(it.get("low_stock_threshold", 5)))

            # Check if product exists
            existing = conn.execute("SELECT id, quantity FROM products WHERE name=? COLLATE NOCASE", (name,)).fetchone()
            if existing:
                # Add to existing stock and update price
                new_qty = existing["quantity"] + qty
                conn.execute("""
                    UPDATE products
                    SET quantity=?, category=?, price=?, cost_price=?, low_stock_threshold=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                """, (new_qty, cat, price, cost, thresh, existing["id"]))
                conn.execute("""
                    INSERT INTO stock_movements(product_id, movement_type, quantity, note)
                    VALUES(?, 'stock_in', ?, 'Document upload restock')
                """, (existing["id"], qty))
            else:
                # Insert new product
                cur = conn.execute("""
                    INSERT INTO products(name, category, quantity, unit, price, cost_price, low_stock_threshold)
                    VALUES(?, ?, ?, ?, ?, ?, ?)
                """, (name, cat, qty, unit, price, cost, thresh))
                conn.execute("""
                    INSERT INTO stock_movements(product_id, movement_type, quantity, note)
                    VALUES(?, 'stock_in', ?, 'Document upload initial stock')
                """, (cur.lastrowid, qty))
            saved_count += 1
    return saved_count

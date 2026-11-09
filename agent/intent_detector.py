import re
from modules.inventory import list_products

ALIASES = {
    "rice": ["rice", "biyyam", "బియ్యం", "వరి", "chawal", "chaawal"],
    "sugar": ["sugar", "panchadara", "పంచదార", "చక్కెర", "cheeni", "chini"],
    "toor dal": ["toor dal", "toor", "kandi pappu", "కందిపప్పు", "పప్పు", "dal", "daal", "arhar"],
    "cooking oil": ["cooking oil", "oil", "noone", "నూనె", "నూని", "tel"],
    "bath soap": ["bath soap", "soap", "soaps", "sabbu", "సబ్బు", "సబ్బులు", "sabun"],
    "tea powder": ["tea powder", "tea", "tee podi", "టీ పొడి", "టీ", "chai", "chai patti"],
    "atta": ["atta", "wheat flour", "wheat", "godhuma pindi", "గోధుమ పిండి", "aata"],
    "milk packets": ["milk packets", "milk", "మిల్క్", "మిల్క్ ప్యాకెట్లు", "paalu", "పాలు", "doodh", "dudh"],
    "biscuits": ["biscuits", "biscuit", "బిస్కెట్లు", "bisket"],
    "turmeric powder": ["turmeric", "pasupu", "పసుపు", "పసుపు పొడి", "haldi"],
    "washing powder": ["washing powder", "surf", "surf excel", "సబ్బు పొడి", "detergent"],
    "salt": ["salt", "tata salt", "uppu", "ఉప్పు", "namak"]
}

TELUGU_DIGITS = {
    '౦': '0', '౧': '1', '౨': '2', '౩': '3', '౪': '4',
    '౫': '5', '౬': '6', '౭': '7', '౮': '8', '౯': '9'
}

def detect_language(text):
    if not text:
        return "en-IN"
    # Check for Telugu Unicode block (ఀ-౿)
    if re.search(r'[ఀ-౿]', text):
        return "te-IN"
    # Check for Devanagari Unicode block (ऀ-ॿ)
    if re.search(r'[ऀ-ॿ]', text):
        return "hi-IN"
    # Check for transliterated Telugu keywords
    tel_trans = ["eeroju", "eroju", "entha", "vachindi", "undhi", "undi", "ammukalu", "ammakam", "kandi", "biyyam", "noone", "panchadara", "chey"]
    lower = text.lower()
    if any(k in lower for k in tel_trans):
        return "te-IN"
    return "en-IN"

def _normalize_text(text):
    res = text
    for td, d in TELUGU_DIGITS.items():
        res = res.replace(td, d)
    return res

def _product_from_text(text):
    raw = _normalize_text(text)
    lower = raw.lower()
    all_prods = list_products()

    # Exact or alias match
    for product in all_prods:
        p_name = product["name"].lower()
        names = [p_name] + ALIASES.get(p_name, [])
        for name in names:
            if re.search(r"^[a-z0-9 ]+$", name):
                if re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", lower):
                    return product
            elif name in raw:
                return product

    # Partial substring match against product name
    for product in all_prods:
        p_name = product["name"].lower()
        if p_name in lower or lower in p_name:
            return product

    return None

def detect_intent(text):
    raw = (text or "").strip()
    norm = _normalize_text(raw)
    lower = norm.lower().replace("-", " ")
    lang = detect_language(raw)

    product = _product_from_text(raw)

    # Extract quantity with units (kg, pcs, packets, litres)
    number_match = re.search(
        r"(?<!\w)(\d+(?:\.\d+)?)\s*(kg|kgs|kilo|kilos|లీటర్లు|లీటర్|litre|liter|litres|l|pcs|pieces|packets|packet|ప్యాకెట్లు|ప్యాకెట్|బాక్సులు|డబ్బాలు)?",
        lower
    )
    quantity = float(number_match.group(1)) if number_match else None

    # Intent detection keywords
    sale_keywords = [
        "sold", "sell", "sale",
        "అమ్మాను", "అమ్మకం", "విక్రయ", "అమ్ము", "అమ్మిన",
        "becha", "bikri", "bech"
    ]
    stock_add_keywords = [
        "add", "restock", "received", "stock in", "bought", "got",
        "చేర్చు", "జోడించు", "వచ్చాయి", "కొను", "కొన్న", "పెంచు", "లభించాయి",
        "aaya", "daalo", "jodo", "kharida"
    ]
    report_keywords = [
        "today", "report", "sales", "revenue", "income", "money", "earned", "earn",
        "how much did i sell", "did i sell", "total sales", "customers", "cash",
        "sell today", "sales today", "how much sales",
        "ఎంత అమ్మ", "ఈరోజు", "నేటి", "రిపోర్ట్", "అమ్మకాలు", "డబ్బు", "ఆదాయం", "కస్టమర్లు", "సేల్",
        "aaj ka", "kamai", "aamdani", "kitna bikri"
    ]
    low_stock_keywords = [
        "low stock", "running low", "out of stock", "shortage", "low",
        "తక్కువ", "స్టాక్ అయిపో", "అయిపోయాయి", "రీస్టాక్", "ఖాలీ",
        "kam stock", "khatam"
    ]
    check_stock_keywords = [
        "stock", "available", "how many", "how much", "quantity", "left", "remaining",
        "ఎన్ని", "ఉన్నాయ", "ఉంది", "ఎంత", "స్టాక్", "మిగిలాయి",
        "kitna hai", "bacha hai"
    ]

    is_low = any(w in lower for w in low_stock_keywords)
    is_report = any(w in lower for w in report_keywords)
    is_sale = any(re.search(r"\b" + re.escape(w) + r"\b", lower) if re.match(r'^[a-z]+$', w) else (w in lower) for w in sale_keywords)
    is_stock_add = any(re.search(r"\b" + re.escape(w) + r"\b", lower) if re.match(r'^[a-z]+$', w) else (w in lower) for w in stock_add_keywords)
    is_check = any(w in lower for w in check_stock_keywords)

    # 1. Product quantity mutations take precedence if product and action are present
    if product and quantity:
        if is_stock_add:
            return {"intent": "add_stock", "product": product, "quantity": quantity, "language": lang}
        if is_sale:
            return {"intent": "record_sale", "product": product, "quantity": quantity, "language": lang}

    # 2. Status & Report queries
    if is_low:
        return {"intent": "low_stock", "language": lang}
    if is_report:
        return {"intent": "daily_report", "language": lang}
    if is_sale:
        return {"intent": "record_sale", "product": product, "quantity": quantity, "language": lang}
    if is_stock_add:
        return {"intent": "add_stock", "product": product, "quantity": quantity, "language": lang}
    if is_check:
        return {"intent": "check_stock", "product": product, "language": lang}

    return {"intent": "help", "language": lang}

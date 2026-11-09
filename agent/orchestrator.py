from agent.intent_detector import detect_intent
from agent.validation import validate_mutation
from modules.inventory import change_stock
from modules.restocking import low_stock_items
from modules.sales import today_summary

def _format_num(value):
    if value is None:
        return "0"
    return str(int(value)) if float(value).is_integer() else f"{float(value):.1f}"

def _format_currency(value):
    val = float(value or 0)
    if val.is_integer():
        return f"₹{int(val):,}"
    return f"₹{val:,.2f}"

def process_command(text, confirmed=False, preferred_lang=None):
    text = (text or "").strip()
    if not text:
        return {"success": False, "reply": "Please type or speak a shop instruction."}

    parsed = detect_intent(text)
    intent = parsed["intent"]
    lang = preferred_lang or parsed.get("language", "en-IN")

    if intent in ("add_stock", "record_sale"):
        error = validate_mutation(parsed)
        if error:
            return {"success": False, "reply": error, "intent": intent}
        product, qty = parsed["product"], parsed["quantity"]
        action = "add" if intent == "add_stock" else "sell"

        if lang == "te-IN":
            act_te = "చేర్చాలా" if intent == "add_stock" else "విక్రయించాలా"
            preview = f"{product['name']} {_format_num(qty)} {product['unit']} {act_te}? ప్రస్తుత స్టాక్: {_format_num(product['quantity'])} {product['unit']}."
        elif lang == "hi-IN":
            act_hi = "जोड़ना चाहते हैं" if intent == "add_stock" else "बेचना चाहते हैं"
            preview = f"क्या आप {product['name']} के {_format_num(qty)} {product['unit']} {act_hi}? वर्तमान स्टॉक: {_format_num(product['quantity'])} {product['unit']}."
        else:
            preview = (f"{action.title()} {_format_num(qty)} {product['unit']} of {product['name']}? "
                       f"Current stock: {_format_num(product['quantity'])} {product['unit']}.")

        if not confirmed:
            return {
                "success": True,
                "requires_confirmation": True,
                "reply": preview,
                "pending": {"intent": intent, "product": product["name"], "quantity": qty},
                "language": lang
            }

        try:
            result = change_stock(product["name"], qty, "stock_in" if intent == "add_stock" else "sale")
        except ValueError as exc:
            return {"success": False, "reply": str(exc), "intent": intent}

        if lang == "te-IN":
            if intent == "add_stock":
                reply = f"పూర్తయింది! {product['name']} స్టాక్ ఇప్పుడు {_format_num(result['quantity'])} {result['unit']}."
            else:
                reply = f"అమ్మకం నమోదైంది! {product['name']} స్టాక్ ఇప్పుడు {_format_num(result['quantity'])} {result['unit']}. అమ్మకం విలువ: {_format_currency(result['sale_total'])}."
        elif lang == "hi-IN":
            if intent == "add_stock":
                reply = f"सम्पन्न हुआ! {product['name']} का स्टॉक अब {_format_num(result['quantity'])} {result['unit']} है।"
            else:
                reply = f"बिक्री दर्ज हुई! {product['name']} का स्टॉक अब {_format_num(result['quantity'])} {result['unit']} है। बिक्री राशि: {_format_currency(result['sale_total'])}."
        else:
            if intent == "add_stock":
                reply = f"Done! {product['name']} stock is now {_format_num(result['quantity'])} {result['unit']}."
            else:
                reply = f"Sale recorded! {product['name']} stock is now {_format_num(result['quantity'])} {result['unit']}. Sale value: ₹{result['sale_total']:.2f}."

        return {"success": True, "reply": reply, "intent": intent, "data": result, "language": lang}

    if intent == "check_stock":
        product = parsed.get("product")
        if not product:
            if lang == "te-IN":
                return {"success": False, "reply": "ఏ వస్తువు స్టాక్ చెక్ చేయాలి? ఉదాహరణకు: 'బియ్యం ఎంత ఉంది?' అని అడగండి.", "language": lang}
            return {"success": False, "reply": "Which product should I check? Try: How much rice is available?", "language": lang}

        if lang == "te-IN":
            reply = f"{product['name']}: {_format_num(product['quantity'])} {product['unit']} అందుబాటులో ఉంది. అమ్మకపు ధర ₹{product['price']:.2f}."
        elif lang == "hi-IN":
            reply = f"{product['name']}: {_format_num(product['quantity'])} {product['unit']} उपलब्ध है। विक्रय मूल्य ₹{product['price']:.2f}."
        else:
            reply = f"{product['name']}: {_format_num(product['quantity'])} {product['unit']} available. Selling price ₹{product['price']:.2f}."
        return {"success": True, "reply": reply, "intent": intent, "product": product, "language": lang}

    if intent == "daily_report":
        report = today_summary()
        revenue = report["revenue"]
        units = report["units"]
        transactions = report["transactions"]
        top_name = report["top_product"]["name"] if report["top_product"] else None

        if revenue == 0 and transactions == 0:
            if lang == "te-IN":
                reply = "ఇంకా ఈరోజు అమ్మకాలు నమోదు కాలేదు."
            elif lang == "hi-IN":
                reply = "आज अभी तक कोई बिक्री दर्ज नहीं हुई है।"
            else:
                reply = "No sales have been recorded for today yet."
            return {"success": True, "reply": reply, "intent": intent, "data": report, "language": lang}

        if lang == "te-IN":
            reply = f"ఈరోజు మీ షాప్‌లో మొత్తం {_format_currency(revenue)} అమ్మకాలు జరిగాయి."
            if transactions > 0:
                reply += f" ({transactions} లావాదేవీలు, {_format_num(units)} యూనిట్లు)."
            if top_name:
                reply += f" అత్యధికంగా అమ్ముడైనది: {top_name}."
        elif lang == "hi-IN":
            reply = f"आज आपकी दुकान में कुल {_format_currency(revenue)} की बिक्री हुई है ({transactions} लेन-देन, {_format_num(units)} यूनिट्स)।"
            if top_name:
                reply += f" सबसे अधिक बिकने वाला उत्पाद: {top_name}."
        else:
            reply = f"Today's sales: {_format_currency(revenue)} across {transactions} transactions. Units sold: {_format_num(units)}."
            if top_name:
                reply += f" Top product: {top_name}."

        return {"success": True, "reply": reply, "intent": intent, "data": report, "language": lang}

    if intent == "low_stock":
        items = low_stock_items()
        if not items:
            if lang == "te-IN":
                reply = "అద్భుతం! ఏ వస్తువూ తక్కువ స్టాక్ పరిమితి కంటే తక్కువగా లేదు."
            elif lang == "hi-IN":
                reply = "बहुत बढ़िया! कोई भी उत्पाद न्यूनतम स्टॉक स्तर से नीचे नहीं है।"
            else:
                reply = "Great! No products are below their low-stock threshold."
            return {"success": True, "reply": reply, "intent": intent, "language": lang}

        names = ", ".join(f"{p['name']} ({_format_num(p['quantity'])} {p['unit']})" for p in items)
        if lang == "te-IN":
            reply = f"ఈ క్రింది వస్తువులు రీస్టాక్ చేయాలి: {names}."
        elif lang == "hi-IN":
            reply = f"इन उत्पादों को पुनः स्टॉक करने की आवश्यकता है: {names}."
        else:
            reply = f"These products need restocking: {names}."
        return {"success": True, "reply": reply, "intent": intent, "data": items, "language": lang}

    # Help fallback
    if lang == "te-IN":
        reply = "నేను మీ షాప్ అమ్మకాలు మరియు స్టాక్‌ను నిర్వహించడంలో సహాయపడతాను. 'ఈరోజు ఎంత సేల్ అయింది?', 'బియ్యం ఎంత ఉంది?', లేదా '10 కేజీల పంచదార చేర్చు' అని అడగండి."
    elif lang == "hi-IN":
        reply = "मैं आपकी दुकान की बिक्री और स्टॉक प्रबंधन में मदद कर सकता हूँ। 'आज की बिक्री कितनी है?', 'चावल कितना बचा है?' या '10 पैकेट बिस्कुट जोड़ो' पूछें।"
    else:
        reply = "I can help with stock and sales. Try: 'Add 5 kg rice', 'Sell 2 soap', 'How much sugar is available?', or 'Show today's sales'."

    return {"success": True, "reply": reply, "intent": "help", "language": lang}

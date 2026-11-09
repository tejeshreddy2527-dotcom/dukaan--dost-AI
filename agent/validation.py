def validate_mutation(parsed):
    if not parsed.get("product"):
        return "I couldn't identify the product. Please use a product already in your catalogue."
    if not parsed.get("quantity") or parsed["quantity"] <= 0:
        return "Please say a quantity greater than zero, for example: add 5 kg rice."
    return None

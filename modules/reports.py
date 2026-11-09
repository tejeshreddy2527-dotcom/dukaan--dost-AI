from modules.sales import today_summary
from modules.restocking import low_stock_items

def daily_report():
    return {"sales": today_summary(), "low_stock": low_stock_items()}

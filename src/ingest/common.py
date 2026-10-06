"""Shared Rossmann record validation. The source files remain untouched."""

from datetime import date

REQUIRED = {
    "Store", "Date", "Sales", "Customers", "Open", "Promo",
    "StateHoliday", "SchoolHoliday",
}


def parse_row(row):
    missing = REQUIRED - row.keys()
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    store = int(row["Store"])
    if store <= 0:
        raise ValueError("Store must be positive")
    day = date.fromisoformat(row["Date"])
    sales = float(row["Sales"])
    if not 0 <= sales < float("inf"):
        raise ValueError("Sales must be a finite nonnegative number")
    open_flag = int(row["Open"])
    promo = int(row["Promo"])
    if open_flag not in (0, 1) or promo not in (0, 1):
        raise ValueError("Open and Promo must be 0 or 1")
    holiday = str(row["StateHoliday"]).strip()
    if holiday not in ("0", "a", "b", "c"):
        raise ValueError(f"unexpected StateHoliday: {holiday}")
    school = int(row["SchoolHoliday"])
    if school not in (0, 1):
        raise ValueError("SchoolHoliday must be 0 or 1")
    return {
        "store_id": store,
        "date": day.isoformat(),
        "sales": sales,
        "customers": int(row["Customers"]),
        "open": open_flag,
        "promo": promo,
        "state_holiday": holiday,
        "school_holiday": school,
        "source": "rossmann-train",
        "schema_version": 1,
    }

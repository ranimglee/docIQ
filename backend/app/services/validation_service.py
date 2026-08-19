from typing import Any


class ValidationService:
    """Checks arithmetic consistency without modifying extracted or reviewed data."""
    def __init__(self, tolerance: float = 0.02) -> None:
        self.tolerance = tolerance

    @staticmethod
    def _value(field: dict[str, Any] | None) -> float | None:
        value = (field or {}).get("value")
        return float(value) if value is not None else None

    def _check(self, name: str, expected: float | None, actual: float | None, message: str) -> dict[str, Any]:
        if expected is None or actual is None:
            return {"name": name, "status": "NOT_CHECKED", "expected": expected, "actual": actual, "difference": None, "message": f"{message}: missing value"}
        difference = round(actual - expected, 2)
        return {"name": name, "status": "PASS" if abs(difference) <= self.tolerance else "FAIL", "expected": round(expected, 2), "actual": round(actual, 2), "difference": difference, "message": message}

    def validate_invoice(self, extraction: dict | None) -> dict[str, Any]:
        extraction = extraction or {}
        financials = extraction.get("financials", {})
        items = extraction.get("items", [])
        checks = []
        for index, item in enumerate(items, 1):
            expected = self._value(item.get("quantity"))
            price = self._value(item.get("unit_price"))
            checks.append(self._check(f"line_item_{index}_amount", expected * price if expected is not None and price is not None else None, self._value(item.get("amount")), f"Line item {index} amount"))
        item_total = sum(self._value(item.get("amount")) or 0 for item in items) if items else None
        subtotal = self._value(financials.get("subtotal")); tax = self._value(financials.get("tax")); total = self._value(financials.get("total")); rate = self._value(financials.get("tax_rate"))
        checks.append(self._check("line_items_sum", item_total, subtotal, "Line items total matches subtotal"))
        checks.append(self._check("tax_calculation", subtotal * rate / 100 if subtotal is not None and rate is not None else None, tax, "Tax calculation"))
        checks.append(self._check("total_calculation", subtotal + tax if subtotal is not None and tax is not None else None, total, "Total calculation"))
        evaluated = [check for check in checks if check["status"] != "NOT_CHECKED"]
        return {"is_valid": bool(evaluated) and all(check["status"] == "PASS" for check in evaluated), "checks": checks}

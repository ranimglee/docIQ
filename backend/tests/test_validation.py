from app.services.validation_service import ValidationService


def field(value): return {"value": value, "confidence": .9}


def test_validation_passes_consistent_invoice():
    data = {"items": [{"quantity": field(20), "unit_price": field(35), "amount": field(700)}], "financials": {"subtotal": field(700), "tax_rate": field(19), "tax": field(133), "total": field(833)}}
    assert ValidationService().validate_invoice(data)["is_valid"] is True


def test_validation_flags_wrong_total():
    data = {"items": [], "financials": {"subtotal": field(100), "tax_rate": field(19), "tax": field(19), "total": field(125)}}
    result = ValidationService().validate_invoice(data)
    assert next(check for check in result["checks"] if check["name"] == "total_calculation")["status"] == "FAIL"

from abc import ABC, abstractmethod
from datetime import datetime
import re
from app.models.document import DocumentType


class InformationExtractor(ABC):
    @abstractmethod
    def extract(self, document_type: DocumentType, text: str) -> dict[str, tuple[str | None, float]]: ...


class RuleBasedExtractor(InformationExtractor):
    _DATE_VALUE = r"(?:[0-3]?\d[/-][01]?\d[/-]\d{2,4}|[0-3]?\d\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})"

    def _match(self, pattern: str, text: str, confidence: float = .8) -> tuple[str | None, float]:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        return (match.group(1).strip(), confidence) if match else (None, 0.0)

    @staticmethod
    def _field(value: str | float | None, confidence: float = 0.0) -> dict[str, str | float | None]:
        """Heuristic confidence estimates, not calibrated model probabilities."""
        return {"value": value, "confidence": confidence if value is not None else 0.0}

    def _date_field(self, label: str, text: str) -> dict[str, str | float | None]:
        value, confidence = self._match(rf"^\s*{label}\s*:\s*({self._DATE_VALUE})\s*$", text, .9)
        if not value:
            return self._field(None)
        for pattern in ("%d %B %Y", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return self._field(datetime.strptime(value, pattern).date().isoformat(), confidence)
            except ValueError:
                continue
        return self._field(None)

    def extract_invoice_structured(self, text: str) -> dict:
        """Extract a conservative invoice representation from OCR reading order."""
        invoice_number, invoice_confidence = self._match(r"^\s*(?:invoice\s*(?:no|number)|inv\s*(?:no|number|#))\s*[:#-]\s*([A-Z0-9][A-Z0-9-]*)\s*$", text, .95)
        currency, currency_confidence = self._match(r"\b(TND|USD|EUR|GBP)\b", text, .9)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        supplier, customer = self._parties_from_lines(lines)
        items = self._items_from_text(text)
        subtotal, subtotal_confidence = self._match(r"^\s*subtotal\s*:?\s*(?:\r?\n\s*)?([\d][\d,.]*)\s*$", text)
        tax, tax_confidence = self._match(r"^\s*(?:tax|vat)(?:\s*\([^)]*\))?\s*:?\s*(?:\r?\n\s*)?([\d][\d,.]*)\s*$", text)
        total, total_confidence = self._match(r"^\s*(?:grand\s+)?total\b\s*:?\s*(?:\r?\n\s*)?([\d][\d,.]*)\s*$", text, .9)
        tax_rate, tax_rate_confidence = self._match(r"^\s*VAT\s*\((\d+(?:\.\d+)?)%\)", text, .8)
        payment = {key: self._field(*self._match(pattern, text, .85)) for key, pattern in {
            "method": r"^\s*Payment Method\s*:\s*([^\r\n]+)", "bank": r"^\s*Bank\s*:\s*([^\r\n]+)",
            "account_holder": r"^\s*Account Holder\s*:\s*([^\r\n]+)", "iban": r"^\s*IBAN\s*:\s*([^\r\n]+)", "reference": r"^\s*Reference\s*:\s*([^\r\n]+)",
        }.items()}
        notes_match = re.search(r"^\s*NOTES\s*$\s*([\s\S]+)$", text, re.IGNORECASE | re.MULTILINE)
        notes = [self._field(line, .7) for line in notes_match.group(1).splitlines() if line.strip()] if notes_match else []
        return {
            "invoice_number": self._field(invoice_number, invoice_confidence), "issue_date": self._date_field("Issue Date", text), "due_date": self._date_field("Due Date", text), "currency": self._field(currency, currency_confidence),
            "supplier": supplier, "customer": customer, "items": items,
            "financials": {"subtotal": self._field(self._number(subtotal), subtotal_confidence), "tax": self._field(self._number(tax), tax_confidence), "tax_rate": self._field(self._number(tax_rate), tax_rate_confidence), "total": self._field(self._number(total), total_confidence)},
            "payment_information": payment, "notes": notes,
        }

    @staticmethod
    def _number(value: str | None) -> float | None:
        return float(value.replace(",", "")) if value else None

    def _parties_from_lines(self, lines: list[str]) -> tuple[dict, dict]:
        blank = lambda: {key: self._field(None) for key in ("name", "address", "email", "phone", "tax_id")}
        supplier, customer = blank(), blank()
        try:
            seller_index, customer_index = lines.index("SELLER"), lines.index("BILL TO")
            supplier["name"] = self._field(lines[customer_index + 1], .8); customer["name"] = self._field(lines[customer_index + 2], .8)
            supplier["address"] = self._field(", ".join(lines[customer_index + 3:customer_index + 5]), .72); customer["address"] = self._field(", ".join(lines[customer_index + 5:customer_index + 7]), .72)
            supplier["email"] = self._field(lines[customer_index + 7], .9); customer["email"] = self._field(lines[customer_index + 8], .9)
            supplier["tax_id"] = self._field(lines[customer_index + 9].replace("Tax ID:", "").strip(), .85); customer["tax_id"] = self._field(lines[customer_index + 10].replace("Tax ID:", "").strip(), .85)
        except (ValueError, IndexError):
            pass
        return supplier, customer

    def _items_from_text(self, text: str) -> list[dict]:
        pattern = re.compile(r"^\s*(.+?)\s*$\r?\n^\s*(\d+(?:\.\d+)?)\s*([A-Za-z]+)?\s*$\r?\n^\s*([\d,.]+)\s*$\r?\n^\s*(\d+(?:\.\d+)?)%\s*$\r?\n^\s*([\d,.]+)\s*$", re.MULTILINE)
        items = []
        for match in pattern.finditer(text):
            description, quantity, unit, unit_price, vat_rate, amount = match.groups()
            if description.lower() in {"description", "subtotal"}:
                continue
            items.append({"description": self._field(description, .9), "quantity": self._field(self._number(quantity), .9), "unit": self._field(unit, .85), "unit_price": self._field(self._number(unit_price), .9), "vat_rate": self._field(self._number(vat_rate), .85), "amount": self._field(self._number(amount), .9)})
        return items

    def extract(self, document_type: DocumentType, text: str) -> dict[str, tuple[str | None, float]]:
        common = {"date": self._match(rf"^\s*(?:issue\s+)?date\s*[:#-]\s*({self._DATE_VALUE})\s*$", text, .9), "currency": self._match(r"\b(TND|USD|EUR|GBP)\b", text, .9)}
        if document_type in (DocumentType.INVOICE, DocumentType.RECEIPT):
            fields = {
                "supplier": self._match(r"^\s*SELLER\s*$\r?\n^\s*BILL TO\s*$\r?\n^\s*([^\r\n]+)", text, .8),
                "invoice_number": self._match(r"^\s*(?:invoice\s*(?:no|number)|inv\s*(?:no|number|#))\s*[:#-]\s*([A-Z0-9][A-Z0-9-]*)\s*$", text, .95),
                "subtotal": self._match(r"^\s*subtotal\s*:?\s*(?:\r?\n\s*)?([\d][\d,.]*)\s*$", text),
                "tax": self._match(r"^\s*(?:tax|vat)(?:\s*\([^)]*\))?\s*:?\s*(?:\r?\n\s*)?([\d][\d,.]*)\s*$", text),
                "total": self._match(r"^\s*(?:grand\s+)?total\b\s*:?\s*(?:\r?\n\s*)?([\d][\d,.]*)\s*$", text, .9),
            }
            return common | fields
        if document_type == DocumentType.CV:
            return {"name": self._match(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})$", text, .65), "email": self._match(r"([\w.+-]+@[\w-]+\.[\w.-]+)", text, .98), "phone": self._match(r"(\+?[\d][\d\s().-]{7,}\d)", text, .9), "skills": self._match(r"skills?\s*[:\n]\s*([^\n]+)", text, .7), "education": self._match(r"education\s*[:\n]\s*([^\n]+)", text, .7), "experience": self._match(r"experience\s*[:\n]\s*([^\n]+)", text, .7)}
        if document_type == DocumentType.CONTRACT:
            return {"title": self._match(r"^(.{3,80}(?:agreement|contract).*)$", text, .7), "parties": self._match(r"between\s+(.{3,150}?)\s+(?:and|,)", text, .65), "date": common["date"], "effective_date": self._match(r"effective(?:\s+date)?\s*[:]?\s*([0-3]?\d[/-][01]?\d[/-]\d{2,4})", text, .9)}
        if document_type == DocumentType.DELIVERY_NOTE:
            return {"supplier": self._match(r"^([A-Z][A-Za-z0-9 &.-]{2,})$", text, .55), "delivery_date": common["date"], "reference": self._match(r"(?:reference|ref)\s*[:#-]?\s*([A-Z0-9-]+)", text, .85), "items": self._match(r"items?\s*[:\n]\s*([^\n]+)", text, .6)}
        return {}

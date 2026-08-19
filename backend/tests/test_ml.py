from app.ml.classifier import BaselineClassifier
from app.ml.extractor import RuleBasedExtractor
from app.models.document import DocumentType


def test_classifier_detects_invoice():
    assert BaselineClassifier().classify("INVOICE\nInvoice No: INV-9\nTotal: 45") == DocumentType.INVOICE


def test_extractor_does_not_invent_total():
    fields = RuleBasedExtractor().extract(DocumentType.INVOICE, "Invoice\nDate: 18/08/2026")
    assert fields["total"] == (None, 0.0)


def test_extractor_finds_email():
    fields = RuleBasedExtractor().extract(DocumentType.CV, "Jane Doe\njane@example.com")
    assert fields["email"][0] == "jane@example.com"


def test_invoice_extraction_does_not_match_heading_or_subtotal_as_total():
    text = """INVOICE
Invoice Number: INV-2026-0087
Issue Date: 19 August 2026
Currency: EUR
 SELLER
BILL TO
TechNova Solutions
 Atlas Digital SARL
Subtotal
1,215.00
VAT (19%)
230.85
TOTAL
1,445.85"""
    fields = RuleBasedExtractor().extract(DocumentType.INVOICE, text)
    assert fields["supplier"][0] == "TechNova Solutions"
    assert fields["invoice_number"][0] == "INV-2026-0087"
    assert fields["date"][0] == "19 August 2026"
    assert fields["tax"][0] == "230.85"
    assert fields["total"][0] == "1,445.85"


def test_structured_invoice_extraction():
    text = """Invoice Number: INV-2026-0087
Issue Date: 19 August 2026
Due Date: 18 September 2026
Currency: EUR
SELLER
BILL TO
TechNova Solutions
Atlas Digital SARL
24 Avenue de la Republique
15 Rue du Lac Turkana
1002 Tunis, Tunisia
1053 Les Berges du Lac, Tunis, Tunisia
billing@technova.example
finance@atlasdigital.example
Tax ID: TN-1234567/A
Tax ID: TN-7654321/B
Full-Stack Web Development
20 h
35.00
19%
700.00
Subtotal
700.00
VAT (19%)
133.00
TOTAL
833.00"""
    result = RuleBasedExtractor().extract_invoice_structured(text)
    assert result["invoice_number"]["value"] == "INV-2026-0087"
    assert result["issue_date"]["value"] == "2026-08-19"
    assert result["supplier"]["name"]["value"] == "TechNova Solutions"
    assert result["items"][0]["amount"]["value"] == 700.0

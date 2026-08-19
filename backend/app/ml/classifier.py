from abc import ABC, abstractmethod
from app.models.document import DocumentType


class DocumentClassifier(ABC):
    @abstractmethod
    def classify(self, text: str) -> DocumentType: ...


class BaselineClassifier(DocumentClassifier):
    """Transparent keyword baseline; replace with LayoutLM/Donut model in V2."""
    def classify(self, text: str) -> DocumentType:
        normalized = text.lower()
        rules = [(DocumentType.INVOICE, ["invoice", "invoice no", "amount due"]), (DocumentType.RECEIPT, ["receipt", "cashier", "change due"]), (DocumentType.CV, ["curriculum vitae", "experience", "education", "skills"]), (DocumentType.CONTRACT, ["agreement", "party", "hereinafter", "terms and conditions"]), (DocumentType.DELIVERY_NOTE, ["delivery note", "delivered to", "dispatch"])]
        return max(rules, key=lambda item: sum(term in normalized for term in item[1]))[0] if any(term in normalized for _, terms in rules for term in terms) else DocumentType.OTHER

"""Acceso de solo lectura al seed de dominio (ADR-001).

Cada repositorio carga su archivo JSON una vez, vía `model_validate_json`
(parseo directo del texto -- nunca pasa por `float`, ver EVIDENCE.md E-05).
Un SKU o cliente ausente devuelve `None`; nunca lanza una excepcion por
"no encontrado" -- eso lo decide validation.py (T6), no el repositorio.
"""

import re
from pathlib import Path

from pydantic import TypeAdapter

from app.domain.models import Customer, InventoryRecord, Policy, Product

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _normalize_reference(reference: str) -> str:
    """BR-02: coincidencia exacta normalizada -- mayusculas, sin espacios ni
    guiones sobrantes. Un SKU no tiene espacios internos legitimos, por eso se
    eliminan todos (no solo se colapsan); los guiones repetidos se colapsan a
    uno. No reescribe el token ni lo aproxima a un SKU valido (eso violaria
    "sin sustitucion por similitud")."""
    text = reference.strip().upper()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"-+", "-", text)
    return text


class CustomerRepository:
    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        raw = (data_dir / "customers.json").read_text(encoding="utf-8")
        customers = TypeAdapter(list[Customer]).validate_json(raw)
        self._by_id: dict[str, Customer] = {c.customer_id: c for c in customers}

    def get(self, customer_id: str) -> Customer | None:
        customer = self._by_id.get(customer_id)
        if customer is None or not customer.active:
            return None
        return customer


class CatalogRepository:
    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        raw = (data_dir / "products.json").read_text(encoding="utf-8")
        products = TypeAdapter(list[Product]).validate_json(raw)
        self._by_normalized_sku: dict[str, Product] = {
            _normalize_reference(p.sku): p for p in products
        }

    def get(self, sku_or_reference: str) -> Product | None:
        product = self._by_normalized_sku.get(_normalize_reference(sku_or_reference))
        if product is None or not product.active:
            return None
        return product


class InventoryRepository:
    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        raw = (data_dir / "inventory.json").read_text(encoding="utf-8")
        records = TypeAdapter(list[InventoryRecord]).validate_json(raw)
        self._by_sku: dict[str, list[InventoryRecord]] = {}
        for record in records:
            self._by_sku.setdefault(record.sku, []).append(record)

    def available(self, sku: str) -> int | None:
        """Disponible total del SKU sumado entre almacenes, o None si no existe."""
        records = self._by_sku.get(sku)
        if records is None:
            return None
        return sum(r.available for r in records)


class PolicyRepository:
    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        raw = (data_dir / "policies.json").read_text(encoding="utf-8")
        self._policy = Policy.model_validate_json(raw)

    def get(self) -> Policy:
        return self._policy

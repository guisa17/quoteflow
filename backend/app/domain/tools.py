"""Herramientas locales de dominio (T9, PROJECT.md §4.2.1, RF-05b).

Envuelven los repositorios (T3, contrato fijo) en cinco funciones con forma
de "herramienta": entrada simple, salida tipada, sin excepciones para el
caso "no encontrado" -- devuelven `None` y quien llama decide que hacer.

Las invoca el grafo (`app/graph/nodes.py`), nunca el modelo. Exponerlas al
LLM como tools enlazadas le daria acceso a inventario y politica, lo que
contradice ADR-002 ("el LLM no accede a inventario ni a politica"). Ninguna
decision vive aqui: eso sigue en `pricing.py`/`policy.py`/`validation.py`
(T4-T6). Este archivo es nuevo (T9); no modifica ninguno de los modulos ya
probados de T2-T6.

Los repositorios se memoizan a nivel de modulo (`lru_cache`) para no releer
y re-parsear el JSON del seed en cada llamada -- son de solo lectura y el
seed no cambia durante la ejecucion del proceso.
"""

from decimal import Decimal
from functools import lru_cache

from pydantic import BaseModel

from app.domain.models import Customer, Policy, Product
from app.domain.repositories import (
    CatalogRepository,
    CustomerRepository,
    InventoryRepository,
    PolicyRepository,
)


class AvailabilityResult(BaseModel):
    """Salida de `check_availability`: disponible total y si cubre lo pedido."""

    sku: str
    available: int
    covers_quantity: bool


@lru_cache
def _customer_repo() -> CustomerRepository:
    return CustomerRepository()


@lru_cache
def _catalog_repo() -> CatalogRepository:
    return CatalogRepository()


@lru_cache
def _inventory_repo() -> InventoryRepository:
    return InventoryRepository()


@lru_cache
def _policy_repo() -> PolicyRepository:
    return PolicyRepository()


def lookup_customer(customer_id: str) -> Customer | None:
    """Cliente y nivel, o ausencia explicita. `resolve_customer` (T9) traduce
    la ausencia a BR-08 (STANDARD provisional + revision humana) -- esta
    funcion no decide nada, solo consulta."""
    return _customer_repo().get(customer_id)


def lookup_product(sku_or_reference: str) -> Product | None:
    """Producto activo del catalogo por coincidencia exacta normalizada
    (BR-02, ya implementada en `CatalogRepository`), o `None` si no existe o
    esta inactivo. Sin sustitucion por similitud."""
    return _catalog_repo().get(sku_or_reference)


def check_availability(sku: str, quantity: int) -> AvailabilityResult | None:
    """`on_hand - reserved` (unico stock cotizable, CLAUDE.md §7) sumado entre
    almacenes, y si cubre `quantity`. `None` si el SKU no tiene registro de
    inventario en absoluto (distinto de disponible = 0)."""
    available = _inventory_repo().available(sku)
    if available is None:
        return None
    return AvailabilityResult(sku=sku, available=available, covers_quantity=quantity <= available)


def get_unit_price(sku: str) -> Decimal | None:
    """Precio de lista del SKU en `Decimal` (BR-04), o `None` si el producto
    no existe en el catalogo."""
    product = _catalog_repo().get(sku)
    return product.list_price_usd if product is not None else None


def get_policy() -> Policy:
    """Maximos de descuento por nivel, techo duro, umbral de aprobacion e
    IGV -- la politica comercial completa (BR-05..BR-09)."""
    return _policy_repo().get()

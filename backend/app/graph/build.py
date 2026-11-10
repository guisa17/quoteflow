"""Compilacion del grafo (T11, ADR-003, RF-07).

Ensambla los 12 nodos (T9) y las 6 rutas condicionales (T10) en un
`StateGraph` compilado con un checkpointer persistente. Interrumpe en
`human_approval` porque ese nodo llama a `interrupt()` internamente
(RF-07) -- no hace falta declarar `interrupt_after` por separado.
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.config import Settings, get_settings
from app.graph import nodes, routing
from app.graph.state import QuoteState
from app.llm.base import Extractor
from app.llm.fake_extractor import FakeExtractor
from app.llm.fallback import FallbackExtractor
from app.llm.gemini_extractor import GeminiExtractor


def _resolve_extractor(settings: Settings) -> Extractor:
    """`fake`: extractor de reglas, sin red (tests y demo sin key).

    `real` + `gemini`: Gemini con respaldo explicito al extractor de reglas
    cuando el proveedor no responde; la procedencia queda en la auditoria.

    `real` + `anthropic`: aun no construido. Falla explicito en vez de
    degradar en silencio."""
    if settings.llm_mode == "fake":
        return FakeExtractor()
    if settings.llm_provider == "gemini":
        primary = GeminiExtractor(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )
        return FallbackExtractor(primary=primary, fallback=FakeExtractor())
    raise NotImplementedError(
        "LLM_PROVIDER=anthropic aun no tiene extractor; usa LLM_PROVIDER=gemini."
    )


def build_graph(
    checkpointer: BaseCheckpointSaver, settings: Settings | None = None
) -> CompiledStateGraph:
    """Compila el grafo completo (T7-T10) con el checkpointer dado.

    `checkpointer` se recibe ya construido (no se abre conexion aqui) para
    que quien llame controle su ciclo de vida -- ver
    `app/graph/checkpointer.py` para la variante respaldada por Postgres."""
    settings = settings or get_settings()
    extractor = _resolve_extractor(settings)

    builder = StateGraph(QuoteState)

    builder.add_node(routing.INGEST, nodes.ingest)
    builder.add_node(routing.EXTRACT, nodes.make_extract_node(extractor))
    builder.add_node(routing.RESOLVE_CUSTOMER, nodes.resolve_customer)
    builder.add_node(routing.VALIDATE_REQUEST, nodes.validate_request)
    builder.add_node(routing.RESOLVE_CATALOG, nodes.resolve_catalog)
    builder.add_node(routing.CHECK_INVENTORY, nodes.check_inventory)
    builder.add_node(routing.PRICE_QUOTE, nodes.price_quote)
    builder.add_node(routing.EVALUATE_POLICY, nodes.evaluate_policy)
    builder.add_node(routing.HUMAN_APPROVAL, nodes.human_approval)
    builder.add_node(routing.APPLY_DECISION, nodes.apply_decision)
    builder.add_node(routing.COMPOSE_DRAFT, nodes.compose_draft)
    builder.add_node(routing.FINALIZE, nodes.finalize)

    builder.add_edge(START, routing.INGEST)
    builder.add_edge(routing.INGEST, routing.EXTRACT)
    builder.add_conditional_edges(routing.EXTRACT, routing.route_after_extract)
    builder.add_edge(routing.RESOLVE_CUSTOMER, routing.VALIDATE_REQUEST)
    builder.add_conditional_edges(routing.VALIDATE_REQUEST, routing.route_after_validate_request)
    builder.add_conditional_edges(routing.RESOLVE_CATALOG, routing.route_after_resolve_catalog)
    builder.add_conditional_edges(routing.CHECK_INVENTORY, routing.route_after_check_inventory)
    builder.add_edge(routing.PRICE_QUOTE, routing.EVALUATE_POLICY)
    builder.add_conditional_edges(routing.EVALUATE_POLICY, routing.route_after_evaluate_policy)
    builder.add_edge(routing.HUMAN_APPROVAL, routing.APPLY_DECISION)
    builder.add_conditional_edges(routing.APPLY_DECISION, routing.route_after_apply_decision)
    builder.add_edge(routing.COMPOSE_DRAFT, routing.FINALIZE)
    builder.add_edge(routing.FINALIZE, END)

    # extract -> resolve_customer no esta en la lista de arriba porque ya lo
    # cubre route_after_extract (arista condicional); resolve_customer solo
    # necesita la arista fija hacia validate_request, ya declarada.

    return builder.compile(checkpointer=checkpointer)

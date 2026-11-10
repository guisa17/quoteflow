"""Corre los casos de `evals/cases.json` contra un extractor y los puntua.

    uv run python -m evals.run                      # Gemini, todos los casos
    uv run python -m evals.run --extractor rules    # extractor de reglas, sin red
    uv run python -m evals.run --only N1-docenas,M2-parafrasis
    uv run python -m evals.run --category manipulacion --model gemini-3.5-flash

Metrica principal: acierto de SKU + cantidad por item (meta >= 90 %,
docs/BUSINESS_CASE.md). Termina con codigo 1 si no se alcanza.
"""

import argparse
import asyncio
import json
import sys
import time
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from langsmith import traceable

from app.config import configure_tracing, get_settings
from app.domain.manipulation import detect_manipulation
from app.domain.models import Extraction
from app.domain.repositories import _normalize_reference
from app.llm.base import ExtractionError, Extractor
from app.llm.fake_extractor import FakeExtractor
from app.llm.gemini_extractor import GeminiExtractor

EVALS_DIR = Path(__file__).resolve().parent
ANY = "*"


@dataclass
class CaseResult:
    id: str
    category: str
    passed: bool
    items_expected: int
    items_matched: int
    failures: list[str] = field(default_factory=list)
    llm_injection_signal: bool | None = None
    latency_ms: int = 0
    error: str | None = None
    got: dict[str, Any] | None = None


def _norm_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def _item_key(reference: str, quantity: int | None) -> tuple[str, int | None]:
    return (_normalize_reference(reference), quantity)


def score(case: dict[str, Any], extraction: Extraction, raw_text: str) -> CaseResult:
    expected = case["expected"]
    failures: list[str] = []

    want = Counter(_item_key(ref, qty) for ref, qty in expected["items"])
    got = Counter(_item_key(i.product_reference, i.quantity) for i in extraction.items)
    matched = sum((want & got).values())
    if want != got:
        failures.append(
            "items: esperado "
            + ", ".join(f"{q} x {r}" for (r, q) in want.elements())
            + " | obtenido "
            + (", ".join(f"{q} x {r}" for (r, q) in got.elements()) or "(nada)")
        )

    exp_site = expected.get("site", ANY)
    if exp_site != ANY:
        ok = (
            extraction.site is None
            if exp_site is None
            else extraction.site is not None and _norm_text(extraction.site) == _norm_text(exp_site)
        )
        if not ok:
            failures.append(f"sede: esperado {exp_site!r} | obtenido {extraction.site!r}")

    exp_disc = expected.get("requested_discount_pct", ANY)
    if exp_disc != ANY:
        got_disc = extraction.requested_discount_pct
        ok = (
            got_disc is None
            if exp_disc is None
            else got_disc is not None and Decimal(str(exp_disc)) == got_disc
        )
        if not ok:
            failures.append(f"descuento: esperado {exp_disc!r} | obtenido {got_disc}")

    exp_inj = expected.get("injection_suspected", ANY)
    if exp_inj != ANY:
        # Lo que decide es el sistema: detector determinista O senal del LLM (BR-18).
        system_signal = bool(detect_manipulation(raw_text)) or extraction.injection_suspected
        if system_signal != exp_inj:
            failures.append(f"manipulacion: esperado {exp_inj} | sistema {system_signal}")

    return CaseResult(
        id=case["id"],
        category=case["category"],
        passed=not failures,
        items_expected=sum(want.values()),
        items_matched=matched,
        failures=failures,
        llm_injection_signal=extraction.injection_suspected,
        got=json.loads(extraction.model_dump_json()),
    )


@traceable(
    run_type="chain",
    name="eval-case",
    process_inputs=lambda inputs: {"case_id": inputs.get("case_id"), "text": inputs.get("text")},
)
async def _extract_case(extractor: Extractor, case_id: str, text: str) -> Extraction:
    """Un caso de evaluacion. Si las trazas estan activas, cada caso es una
    traza en LangSmith con su id y categoria como metadatos."""
    return await extractor.extract(text)


def build_extractor(kind: str, model: str | None) -> tuple[Extractor, str]:
    settings = get_settings()
    # Proyecto aparte, para no mezclar las corridas de evals con el uso normal.
    if configure_tracing(
        settings.model_copy(update={"langsmith_project": f"{settings.langsmith_project}-evals"})
    ):
        print(f"Trazas en LangSmith: proyecto {settings.langsmith_project}-evals")
    if kind == "rules":
        return FakeExtractor(), "reglas locales"
    if not settings.gemini_api_key:
        sys.exit("Falta GEMINI_API_KEY en backend/.env (ver evals/README.md).")
    chosen = model or settings.gemini_model
    return GeminiExtractor(settings.gemini_api_key, chosen, settings.llm_timeout_seconds), chosen


async def run(args: argparse.Namespace) -> int:
    data = json.loads((EVALS_DIR / "cases.json").read_text(encoding="utf-8"))
    cases = data["cases"]
    if args.only:
        wanted = set(args.only.split(","))
        cases = [c for c in cases if c["id"] in wanted]
    if args.category:
        cases = [c for c in cases if c["category"] == args.category]
    if not cases:
        sys.exit("Ningun caso coincide con el filtro.")

    extractor, label = build_extractor(args.extractor, args.model)
    print(f"Extractor: {label} · {len(cases)} casos\n")

    results: list[CaseResult] = []
    for n, case in enumerate(cases):
        if n and args.extractor == "gemini":
            await asyncio.sleep(args.delay)  # cuota por minuto del plan gratuito
        start = time.perf_counter()
        try:
            extraction = await _extract_case(
                extractor,
                case["id"],
                case["text"],
                langsmith_extra={
                    "metadata": {"case_id": case["id"], "category": case["category"]},
                    "tags": [case["category"]],
                },
            )
            result = score(case, extraction, case["text"])
        except ExtractionError as exc:
            expected_items = len(case["expected"]["items"])
            result = CaseResult(
                id=case["id"],
                category=case["category"],
                passed=False,
                items_expected=expected_items,
                items_matched=0,
                error=f"{type(exc).__name__}: {exc}",
            )
        result.latency_ms = round((time.perf_counter() - start) * 1000)
        results.append(result)

        status = "OK   " if result.passed else "FALLA"
        print(f"{status} {result.id:<24} {result.latency_ms:>6} ms")
        for failure in result.failures:
            print(f"      - {failure}")
        if result.error:
            print(f"      - error: {result.error}")
        if "known_issue" in case:
            print(f"      (conocido) {case['known_issue']}")

    items_expected = sum(r.items_expected for r in results)
    items_matched = sum(r.items_matched for r in results)
    item_accuracy = items_matched / items_expected if items_expected else 0.0
    passed = sum(r.passed for r in results)
    errors = sum(r.error is not None for r in results)
    latencies = [r.latency_ms for r in results if r.error is None]

    print("\nResumen")
    print(
        f"  SKU + cantidad:   {items_matched}/{items_expected} items "
        f"({item_accuracy:.0%}) · meta {args.threshold:.0%}"
    )
    print(f"  Casos completos:  {passed}/{len(results)}")
    for category in sorted({r.category for r in results}):
        group = [r for r in results if r.category == category]
        print(f"    {category:<18} {sum(r.passed for r in group)}/{len(group)}")
    print(f"  Errores:          {errors}")
    if latencies:
        print(f"  Latencia media:   {sum(latencies) // len(latencies)} ms")

    out_dir = EVALS_DIR / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = out_dir / f"{stamp}-{label.replace(' ', '-')}.json"
    out_file.write_text(
        json.dumps(
            {
                "extractor": label,
                "cases_version": data["version"],
                "item_accuracy": round(item_accuracy, 4),
                "cases_passed": passed,
                "cases_total": len(results),
                "results": [asdict(r) for r in results],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nResultado guardado en {out_file.relative_to(EVALS_DIR.parent)}")
    return 0 if item_accuracy >= args.threshold else 1


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Evalua el extractor contra evals/cases.json")
    parser.add_argument("--extractor", choices=["gemini", "rules"], default="gemini")
    parser.add_argument("--model", help="modelo de Gemini (por defecto, GEMINI_MODEL)")
    parser.add_argument("--only", help="ids separados por coma")
    parser.add_argument("--category", help="solo una categoria de casos")
    parser.add_argument("--delay", type=float, default=4.0, help="segundos entre llamadas")
    parser.add_argument("--threshold", type=float, default=0.9)
    sys.exit(asyncio.run(run(parser.parse_args())))


if __name__ == "__main__":
    main()

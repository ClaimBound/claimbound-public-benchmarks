#!/usr/bin/env python3
"""Render a ClaimBound evidence-card SVG from a validated JSON card."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from textwrap import shorten
from typing import Any
from xml.sax.saxutils import escape


DEFAULT_TEMPLATE = Path("docs/assets/claimbound_evidence_card.svg")


def render_svg(card_path: Path, template_path: Path = DEFAULT_TEMPLATE) -> str:
    card = json.loads(card_path.read_text(encoding="utf-8"))
    if not isinstance(card, dict):
        raise ValueError("evidence card must be a JSON object")

    template = template_path.read_text(encoding="utf-8")
    values = _visual_values(card)

    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", escape(value))

    unresolved = sorted(set(_find_placeholders(rendered)))
    if unresolved:
        raise ValueError("unresolved SVG placeholders: " + ", ".join(unresolved))

    return rendered


def _visual_values(card: dict[str, Any]) -> dict[str, str]:
    visual = card.get("visual_summary")
    if not isinstance(visual, dict):
        visual = {}

    evidence_id = str(card.get("evidence_id", ""))
    protocol_id = str(card.get("protocol_id", ""))
    result_status = str(card.get("result_status", ""))
    reproduction_level = str(card.get("reproduction_level", ""))
    source_name = str(card.get("official_source_name", ""))

    return {
        "status_exact": _fit(result_status, 23),
        "reproduction_level": _fit(_short_reproduction(reproduction_level), 21),
        "allowed_claim_sentence": _fit(
            _first(visual, "allowed_claim_sentence", card.get("allowed_claim_sentence")),
            46,
        ),
        "record_id": _fit(_record_id(evidence_id), 24),
        "protocol_id": _fit(protocol_id, 31),
        "target_definition": _fit(_first(visual, "target_definition", card.get("domain")), 27),
        "candidate_definition": _fit(_first(visual, "candidate_definition", source_name), 24),
        "controls_and_gate": _fit(
            _first(visual, "controls_and_gate", card.get("baseline_control_summary")),
            35,
        ),
        "source_name": _fit(source_name, 31),
        "period_scope": _fit(_first(visual, "period_scope", card.get("access_date")), 25),
        "evidence_date": _fit(str(card.get("access_date", "")), 14),
        "artifact_ref": _fit(
            _first(
                visual,
                "artifact_ref",
                card.get("sanitized_report_path"),
            ),
            35,
        ),
        "evidence_url": _fit(
            _first(visual, "evidence_url", f"docs/evidence_cards/{evidence_id}.json"),
            62,
        ),
    }


def _first(mapping: dict[str, Any], key: str, fallback: object) -> str:
    value = mapping.get(key)
    if value is None or str(value).strip() == "":
        value = fallback
    return str(value or "")


def _record_id(evidence_id: str) -> str:
    if evidence_id.startswith("CLAIMBOUND-"):
        evidence_id = evidence_id.removeprefix("CLAIMBOUND-")
    if "-2026-" in evidence_id:
        evidence_id = evidence_id.split("-2026-", 1)[0]
    return evidence_id


def _short_reproduction(value: str) -> str:
    value = value.strip()
    if value.lower() == "not independently reproduced":
        return "NOT INDEPENDENT"
    if value == "REPRODUCED_OUTCOME_WITH_SOURCE_BYTE_DRIFT":
        return "OUTCOME + DRIFT"
    return value


def _fit(value: str, width: int) -> str:
    normalized = " ".join(value.split())
    return shorten(normalized, width=width, placeholder="...") if normalized else "n/a"


def _find_placeholders(text: str) -> list[str]:
    out: list[str] = []
    start = 0
    while True:
        left = text.find("{{", start)
        if left == -1:
            break
        right = text.find("}}", left + 2)
        if right == -1:
            break
        out.append(text[left + 2 : right])
        start = right + 2
    return out


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("card", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    svg = render_svg(args.card, args.template)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8")
    print(f"rendered_svg={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

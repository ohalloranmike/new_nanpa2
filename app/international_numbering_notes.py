"""Curated national numbering notes not yet surfaced by libphonenumber special-type metadata."""

from __future__ import annotations

from typing import TypedDict


class NumberingNoteReference(TypedDict):
    name: str
    url: str


class NumberingNote(TypedDict):
    title: str
    effective_date: str
    paragraphs: list[str]
    references: list[NumberingNoteReference]


# ISO 3166-1 alpha-2 → notes shown on /international/{iso2} only.
NUMBERING_NOTES: dict[str, list[NumberingNote]] = {
    "ES": [
        {
            "title": "Commercial outbound calls (400 range)",
            "effective_date": "17 October 2026",
            "paragraphs": [
                "Spain has assigned nine-digit national numbers beginning with 400 for outbound "
                "commercial calls. From 17 October 2026, covered businesses are expected to "
                "originate applicable commercial and sales outbound traffic from the 400 range "
                "rather than from ordinary geographic or other Spanish numbers.",
                "400 numbers are outbound-only: they identify commercial calling parties but "
                "are not intended to receive inbound calls. Existing Spanish numbers may still "
                "be used for customer service, inbound calls, and other permitted uses outside "
                "covered commercial outbound calling.",
            ],
            "references": [
                {
                    "name": "BOE resolution on 400 commercial numbering (April 2026)",
                    "url": "https://www.boe.es/buscar/act.php?id=BOE-A-2026-8409",
                },
                {
                    "name": "CNMC numbering register",
                    "url": "https://sede.cnmc.gob.es/tramites/telecomunicaciones/registro-de-numeracion",
                },
            ],
        },
    ],
}


def numbering_notes_for_country(iso2: str) -> list[NumberingNote]:
    """Return curated notes for a country, or an empty list."""
    return list(NUMBERING_NOTES.get((iso2 or "").strip().upper(), []))

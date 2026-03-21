"""
Welke URL’s zijn relevant voor een patiënt-/klant-AI (call agent)?
Voor domeinen met een vaste padlijst: zelfde regels als ingest_wgk --scope patient_extended.
Voor andere sites: generieke uitsluiting, met o.a. stages/zorgpartner/sollicitatie-contact toegestaan
(niet: vacature-index, nieuws, admin, …).
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

# Zelfde als ingest_wgk.py
_POSTCODE_LOCALITY_SLUG = re.compile(r"^\d{4}-")


def path_segments(url: str) -> list[str]:
    return [p for p in urlparse(url).path.split("/") if p]


def _is_wgk_host(hostname: str) -> bool:
    h = (hostname or "").lower().split("@")[-1].strip()
    return h == "witgelekruis.be" or h.endswith(".witgelekruis.be")


def is_wgk_patient_public_url(url: str, *, extended: bool = False) -> bool:
    """Spiegel van ingest_wgk.is_patient_public_url(..., extended=...)."""
    parts = path_segments(url)
    if not parts:
        return True

    noise_roots = (
        "artikel",
        "nieuws",
        "jobs",
        "evenement",
        "recepten",
        "in-jouw-buurt",
        "node",
        "pers",
    )
    if not extended:
        noise_roots = noise_roots + (
            "stages",
            "voor-zorgpartners",
            "info-voor-zorgpartners",
        )
    if parts[0] in noise_roots:
        return False

    if not extended and parts[0] in ("contacteer-ons-jobs", "solliciteer-nu", "spontane-sollicitatie"):
        return False

    if parts[0] == "thuisverpleging-thuiszorgdiensten" and len(parts) > 2:
        return False

    if parts[0] == "thuisverpleging-en-thuiszorgdiensten" and len(parts) >= 3:
        if _POSTCODE_LOCALITY_SLUG.match(parts[2]):
            return False

    patient_roots = (
        "praktisch",
        "praktische-informatie",
        "thuisverpleging-en-thuiszorgdiensten",
        "thuisverpleging-thuiszorgdiensten",
        "over-ons",
        "contacteer-ons",
        "ombudsdienst",
        "klachtenregistratie",
        "privacy-policy",
        "mijnwgk",
        "thuisverpleging",
        "disclaimer",
        "toegankelijkheidsverklaring",
        "remgeld",
        "home",
    )
    if extended:
        patient_roots = patient_roots + (
            "stages",
            "voor-zorgpartners",
            "info-voor-zorgpartners",
            "contacteer-ons-jobs",
            "solliciteer-nu",
            "spontane-sollicitatie",
        )
    return parts[0] in patient_roots


# Ruwe uitsluiting; portal gebruikt altijd “extended”: deze segmenten blijven wél toegestaan.
_GENERIC_ALLOW_EXTENDED = frozenset(
    {
        "stages",
        "stage",
        "internships",
        "voor-zorgpartners",
        "info-voor-zorgpartners",
        "zorgpartners",
        "solliciteer-nu",
        "spontane-sollicitatie",
        "contacteer-ons-jobs",
    }
)

_GENERIC_EXCLUDE_FIRST = frozenset(
    {
        "artikel",
        "nieuws",
        "news",
        "blog",
        "jobs",
        "job",
        "vacatures",
        "vacature",
        "careers",
        "werken-bij",
        "evenement",
        "evenementen",
        "events",
        "event",
        "recepten",
        "recipes",
        "stages",
        "stage",
        "internships",
        "voor-zorgpartners",
        "info-voor-zorgpartners",
        "zorgpartners",
        "pers",
        "press",
        "in-jouw-buurt",
        "node",
        "wp-admin",
        "wp-login",
        "wp-json",
        "admin",
        "login",
        "register",
        "cart",
        "checkout",
        "account",
        "mijn-account",
        "solliciteer-nu",
        "spontane-sollicitatie",
        "contacteer-ons-jobs",
        "feed",
        "rss",
        "api",
        "author",
        "tag",
        "category",
        "categories",
    }
)

_GENERIC_EXCLUDE_PORTAL = frozenset(_GENERIC_EXCLUDE_FIRST - _GENERIC_ALLOW_EXTENDED)


def is_generic_customer_facing_url(url: str) -> bool:
    parts = path_segments(url)
    if not parts:
        return True
    first = parts[0].lower()
    return first not in _GENERIC_EXCLUDE_PORTAL


def url_allowed_for_call_agent(url: str, site_hostname: str) -> tuple[bool, str]:
    """Returns (allowed, reason_if_not). Altijd de ruimere (extended-equivalent) padset."""
    if _is_wgk_host(site_hostname):
        if is_wgk_patient_public_url(url, extended=True):
            return True, ""
        return False, "niet in padfilter (site-specifieke padlijst)"

    if is_generic_customer_facing_url(url):
        return True, ""
    return False, "uitgesloten pad (nieuws/admin/jobs-index/…)"


def filter_urls_for_call_agent(site_hostname: str, urls: list[str]) -> list[str]:
    return [u for u in urls if url_allowed_for_call_agent(u, site_hostname)[0]]

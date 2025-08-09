from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Literal


def _parse_simple_yaml(content: str) -> Dict[str, Dict[str, List[str]]]:
    """A minimal YAML parser for the expected rules structure.

    Supports a limited subset:
    - Top-level mapping keys (e.g., official:, reseller:, suspect:)
    - One level nested keys (e.g., exact:, regex:)
    - List values on a single line using JSON-like syntax with double quotes, e.g. ["a", "b"]
    """
    rules: Dict[str, Dict[str, List[str]]] = {}
    current_section: str | None = None

    for raw_line in content.splitlines():
        line = raw_line.rstrip("\n\r")
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        # Top-level key (no leading spaces)
        if not line.startswith(" ") and line.endswith(":"):
            current_section = line[:-1].strip()
            rules.setdefault(current_section, {})
            continue

        # Nested key-value lines
        if current_section is None:
            continue

        stripped = line.strip()
        if ":" not in stripped:
            continue

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()

        items: List[str] = []
        if value.startswith("[") and value.endswith("]"):
            # Extract items enclosed in double quotes
            items = re.findall(r'"([^"]*)"', value)

        rules[current_section][key] = items

    return rules


def load_rules(path: str = "config/seller_rules.yaml") -> Dict[str, Dict[str, List[str]]]:
    """Load seller labeling rules from a YAML file.

    Attempts to use PyYAML if available; falls back to a minimal parser
    that supports the specific structure used by this project.
    """
    rules_path = Path(path)
    if not rules_path.exists():
        raise FileNotFoundError(f"Rules file not found: {rules_path}")

    text = rules_path.read_text(encoding="utf-8")

    # First, try to use PyYAML if it exists. If anything goes wrong, fall back.
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text) or {}
        normalized: Dict[str, Dict[str, List[str]]] = {}

        for label, section in (loaded or {}).items():
            if not isinstance(section, dict):
                continue
            inner: Dict[str, List[str]] = {}
            for key in ("exact", "regex"):
                raw = section.get(key, [])
                if raw is None:
                    raw = []
                if not isinstance(raw, list):
                    raw = [str(raw)]
                inner[key] = [str(item) for item in raw]
            normalized[label] = inner

        return normalized
    except Exception:
        return _parse_simple_yaml(text)


def _match_exact(name: str, patterns: List[str]) -> bool:
    return any(name == pattern for pattern in patterns)


def _match_regex(name: str, patterns: List[str]) -> bool:
    for pattern in patterns:
        try:
            if re.search(pattern, name):
                return True
        except re.error:
            # If a pattern is not a valid regex, treat it as a plain substring.
            if pattern and pattern in name:
                return True
    return False


def label_seller(
    mall_name: str, rules: Dict[str, Dict[str, List[str]]]
) -> Literal["official", "reseller", "suspect"]:
    """Label a mall name as "official", "reseller", or "suspect".

    Precedence: official > reseller > suspect. Empty or None is labeled as "suspect".

    Doctests:
        >>> r = load_rules("config/seller_rules.yaml")
        >>> label_seller("올리브영", r)
        'official'
        >>> label_seller("아모레퍼시픽공식", r)
        'official'
        >>> label_seller("랜덤공식스토어", r)
        'official'
        >>> label_seller("쿠팡", r)
        'reseller'
        >>> label_seller("무배특가샵", r)
        'suspect'
        >>> label_seller("", r)
        'suspect'
    """
    if mall_name is None or mall_name.strip() == "":
        return "suspect"

    name = mall_name.strip()

    official = rules.get("official", {})
    reseller = rules.get("reseller", {})
    suspect = rules.get("suspect", {})

    official_exact = official.get("exact", []) or []
    official_regex = official.get("regex", []) or []
    reseller_regex = reseller.get("regex", []) or []
    suspect_regex = suspect.get("regex", []) or []

    if _match_exact(name, official_exact) or _match_regex(name, official_regex):
        return "official"

    if _match_regex(name, reseller_regex):
        return "reseller"

    if _match_regex(name, suspect_regex):
        return "suspect"

    # Default when nothing matches
    return "suspect"


if __name__ == "__main__":
    import doctest

    doctest.testmod()
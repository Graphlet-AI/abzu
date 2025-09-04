import re

import cleanco
import pandas as pd
from stop_words import AVAILABLE_LANGUAGES, get_stop_words


def get_multilingual_stop_words() -> set:
    """
    Get a list of ALL common stop words across languages.
    """
    stop_words: set = set()
    for lang in AVAILABLE_LANGUAGES:
        stop_words.update(get_stop_words(lang))
    return stop_words


def get_corporate_ending(company_name: str) -> str | None:
    """Extract corporate ending by finding what basename removed"""
    if not company_name:
        return None

    cleaned = cleanco.basename(company_name)

    # If nothing was removed, there's no ending
    if cleaned == company_name:
        return None

    # The ending is everything after the basename
    # Find where cleaned ends in the original string
    cleaned_len = len(cleaned)
    ending = company_name[cleaned_len:].strip()

    return ending if ending else None


def get_basename(name: str) -> str | None:
    """
    Get the cleaned basename of a company name.
    Cleans using cleanco and returns the cleaned name.
    """
    if pd.isna(name) or name is None:
        return None

    # Clean the company name using cleanco
    cleaned_name = cleanco.basename(name)
    return cleaned_name.strip() if cleaned_name else None


def get_acronyms(name: str) -> str | None:

    # Remove any starting dollar sign
    if name.startswith("$"):
        name = name[1:]

    # Remove any parenthesis
    name = re.sub(r"\(.*?\)", "", name)

    # Clean the company name using cleanco
    cleaned_name = cleanco.basename(name)

    acronym: str | None = None
    if cleaned_name:
        # Split into words on both spaces and hyphens for acronym generation
        words: list[str] = re.split(r"[ -]+", cleaned_name)
        # Remove empty strings that might result from splitting
        words = [w for w in words if w]

        # Filter out common words and lowercase single letters (keep uppercase single letters)
        stop_words: set[str] = get_multilingual_stop_words()
        meaningful_words: list[str] = [
            w
            for w in words
            if (len(w) == 1 and w.isupper()) or (len(w) > 1 and w.lower() not in stop_words)
        ]

        if meaningful_words and len(meaningful_words) > 1:  # Only process if more than one word
            # Create standard abbreviation (first letter of each word that is uppercase)
            acronym = "".join([w[0].upper() for w in meaningful_words])

        # If there's only one meaningful uppercase word, add it as the abbreviation
        if len(meaningful_words) == 1 and meaningful_words[0].isupper():
            acronym = meaningful_words[0].upper()

    return acronym

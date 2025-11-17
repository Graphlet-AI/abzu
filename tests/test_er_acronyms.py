import pandas as pd

from abzu.er.acronyms import (
    get_acronyms,
    get_basename,
    get_corporate_ending,
    get_multilingual_stop_words,
)


def test_get_multilingual_stop_words():
    """Test that multilingual stop words are properly loaded."""
    stop_words = get_multilingual_stop_words()

    assert isinstance(stop_words, set)
    assert len(stop_words) > 0

    # Test that common English stop words are included
    assert "the" in stop_words
    assert "and" in stop_words
    assert "of" in stop_words

    # Test that common non-English stop words are included
    assert "le" in stop_words  # French
    assert "der" in stop_words  # German
    assert "el" in stop_words  # Spanish


def test_get_corporate_ending():
    """Test corporate ending extraction that returns str | None."""
    # Test with common corporate endings
    assert get_corporate_ending("Apple Inc.") == "Inc."
    assert get_corporate_ending("Microsoft Corporation") == "Corporation"
    assert get_corporate_ending("Google LLC") == "LLC"
    assert get_corporate_ending("Tesla, Inc.") == ", Inc."

    # Test with no corporate ending - now returns None
    assert get_corporate_ending("Apple") is None
    assert get_corporate_ending("Google") is None
    assert get_corporate_ending("Nike") is None

    # Test edge cases
    assert get_corporate_ending("") is None

    # Test with whitespace
    result = get_corporate_ending("Apple Inc. ")
    expected = get_corporate_ending("Apple Inc.")
    assert result == expected


def test_get_basename():
    """Test basename extraction function."""
    # Test with corporate endings - should remove them
    assert get_basename("Apple Inc.") == "Apple"
    assert get_basename("Microsoft Corporation") == "Microsoft"
    assert get_basename("Google LLC") == "Google"
    assert (
        get_basename("International Business Machines Corporation")
        == "International Business Machines"
    )

    # Test with no corporate ending - should return as-is
    assert get_basename("Apple Computer") == "Apple Computer"
    assert get_basename("Nike") == "Nike"

    # Test edge cases with pandas NA
    assert get_basename(pd.NA) is None  # type: ignore[arg-type]
    assert get_basename("") is None

    # Test with whitespace
    assert get_basename("Apple Inc. ") == "Apple"


def test_get_acronyms_multi_word():
    """Test multi-word company acronym generation."""
    # Multi-word companies should work
    result = get_acronyms("Apple Computer Inc.")
    assert result == "AC"

    # Longer company names should work
    result = get_acronyms("International Business Machines Corporation")
    assert result == "IBM"

    # Test with stop words filtering
    result = get_acronyms("The Apple Computer Company")
    assert result == "AC"  # "The" filtered out, "Company" is ending

    # Test three-word acronym
    result = get_acronyms("Advanced Micro Devices Inc.")
    assert result == "AMD"


def test_get_acronyms_single_word():
    """Test single-word companies return None."""
    # Single words after cleaning should return None
    assert get_acronyms("Apple Inc.") is None  # "Apple" after cleaning
    assert get_acronyms("Google LLC") is None  # "Google" after cleaning
    assert get_acronyms("Tesla Corporation") is None  # "Tesla" after cleaning
    assert get_acronyms("Nike") is None  # No corporate ending, single word


def test_get_acronyms_single_uppercase_word():
    """Test special case for single uppercase words."""
    # Single uppercase word should be returned as acronym
    result = get_acronyms("IBM Corporation")
    assert result == "IBM"

    # Test with other single uppercase words
    result = get_acronyms("AMD Inc.")
    assert result == "AMD"

    # Mixed case single words should return None
    assert get_acronyms("Apple Inc.") is None  # "Apple" is not all uppercase


def test_get_acronyms_none_input():
    """Test None input handling."""
    # Function correctly returns None for pandas NA input
    result = get_acronyms(pd.NA)  # type: ignore[arg-type]
    assert result is None


def test_get_acronyms_edge_cases():
    """Test edge cases that work correctly."""
    # Empty string returns None
    assert get_acronyms("") is None

    # Whitespace only returns None
    assert get_acronyms("   ") is None

    # Tab and newline whitespace
    assert get_acronyms("\t\n") is None


def test_get_acronyms_stop_words():
    """Test stop word filtering."""
    # Test with stop words
    result = get_acronyms("The International Business Machines Corporation")
    assert result == "IBM"  # "The" filtered out

    # Test with multiple stop words
    result = get_acronyms("The Advanced Micro Devices Corporation")
    assert result == "AMD"

    # Test all stop words
    assert get_acronyms("The And Of Company") is None


def test_get_acronyms_single_letters():
    """Test uppercase single letter inclusion in acronyms."""
    # Test name with uppercase single letter words
    result = get_acronyms("Apple A Computer Inc.")
    assert result == "AAC"  # Uppercase "A" should be included

    # Test name with lowercase single letter words
    result = get_acronyms("Apple a Computer Inc.")
    assert result == "AC"  # Lowercase "a" should be filtered out

    # Test with multiple uppercase single letters
    result = get_acronyms("A B C Computer Systems Inc.")
    assert result == "ABCCS"  # All uppercase letters should be included

    # Test all uppercase single letters - should create acronym
    assert get_acronyms("A B C Company") == "ABC"


def test_get_acronyms_insufficient_words():
    """Test cases with insufficient meaningful words."""
    # Only stop words - should return None
    assert get_acronyms("The And Of Company") is None

    # Single meaningful word after filtering - should return None
    assert get_acronyms("Apple The And Inc.") is None  # Only "Apple" remains

    # Single letter words - should create acronym
    assert get_acronyms("A B C Company") == "ABC"  # Single letters should be included


def test_get_acronyms_case_handling():
    """Test case handling."""
    # Mixed case should work
    result = get_acronyms("apple computer inc.")
    assert result == "AC"

    # Already uppercase should work
    result = get_acronyms("APPLE COMPUTER INC.")
    assert result == "AC"

    # Title case should work
    result = get_acronyms("Apple Computer Inc.")
    assert result == "AC"


def test_get_acronyms_whitespace():
    """Test whitespace handling."""
    # Extra spaces should work
    result = get_acronyms("  Apple  Computer  Inc.  ")
    assert result == "AC"

    # Test with tabs (if split handles them)
    result = get_acronyms("Apple\tComputer\tInc.")
    assert result == "AC"


def test_get_acronyms_complex_names():
    """Test complex company names."""
    # Test with punctuation
    result = get_acronyms("Advanced Micro Devices, Inc.")
    assert result == "AMD"

    # Test with numbers (single characters are NOT filtered, only len > 1 check)
    result = get_acronyms("3M Computer Systems Inc.")
    assert result == "3CS"  # "3" and "M" are included as single characters

    # Test with ampersand
    result = get_acronyms("Johnson & Johnson Inc.")
    assert result == "JJ"  # "&" should be filtered as single character


def test_get_acronyms_punctuation():
    """Test handling of punctuation in company names."""
    # Commas in corporate endings
    result = get_acronyms("Tesla, Inc.")
    assert result is None  # "Tesla" is single word

    # Hyphens should be split for acronym generation
    result = get_acronyms("Coca-Cola Company")
    assert result == "CC"  # "Coca" and "Cola" should be split


def test_get_acronyms_no_meaningful_words():
    """Test when no meaningful words remain after filtering."""
    # All punctuation
    assert get_acronyms("!!! @@@ ### Corporation") is None

    # All numbers (single characters are NOT filtered)
    assert get_acronyms("123 456 789 Inc.") == "147"  # Numbers treated as single chars

    # Mixed punctuation and uppercase single letters (punctuation filtered)
    assert (
        get_acronyms("A ! B @ C # Company") == "ABC"
    )  # Uppercase letters included, punctuation filtered


def test_get_acronyms_boundary_cases():
    """Test boundary cases around the word count logic."""
    # Exactly two meaningful words
    result = get_acronyms("Apple Computer")
    assert result == "AC"

    # Three meaningful words
    result = get_acronyms("Apple Computer Systems")
    assert result == "ACS"

    # One meaningful word (should return None unless uppercase)
    assert get_acronyms("Apple") is None

    # One uppercase word
    result = get_acronyms("IBM")
    assert result == "IBM"


def test_get_acronyms_stop_words_and_letters_combined():
    """Test combined filtering of stop words and single letters."""
    # Mix of stop words and single letters
    result = get_acronyms("The A Apple B Computer C Inc.")
    assert result == "AABCC"  # Stop words filtered, single letters included

    # Stop words between meaningful words
    result = get_acronyms("Apple And Computer Systems")
    assert result == "ACS"  # "And" filtered out


def test_get_acronyms_corporate_endings_not_in_acronym():
    """Test that corporate endings don't appear in the acronym."""
    # Should not include corporate endings in acronyms
    result = get_acronyms("Apple Computer Inc.")
    assert result == "AC"  # No "I" from "Inc."

    result = get_acronyms("Google Search LLC")
    assert result == "GS"  # No "L" from "LLC"

    result = get_acronyms("Microsoft Systems Corporation")
    assert result == "MS"  # No "C" from "Corporation"


def test_get_acronyms_empty_after_cleaning():
    """Test when cleanco returns empty string."""
    # This is harder to test without mocking cleanco, but we can try edge cases
    # If cleanco returns empty/None, acronym should remain None

    # Strings that might not clean well (theoretical)
    result = get_acronyms("...")
    assert result is None

    result = get_acronyms("   Inc.   ")
    assert result is None  # Only corporate ending, no base name


def test_get_acronyms_hyphenated_names():
    """Test hyphenated company names."""
    # Simple hyphenated name
    result = get_acronyms("X-FAB")
    assert result == "XF"  # Should create acronym from parts

    # Hyphenated name with corporate ending
    result = get_acronyms("Coca-Cola Company")
    assert result == "CC"  # Should split on hyphen

    # Multiple hyphens
    result = get_acronyms("Jean-Luc-Picard Corporation")
    assert result == "JLP"  # Should split all hyphen parts

    # Mixed spaces and hyphens
    result = get_acronyms("Advanced Micro-Devices Inc.")
    assert result == "AMD"  # Should handle both separators

    # Hyphen with stop words
    result = get_acronyms("The Coca-Cola Company")
    assert result == "CC"  # "The" filtered, hyphen split

    # Single hyphenated word after cleaning should return None
    result = get_acronyms("Jean-Luc Corporation")
    assert result == "JL"  # Should split even though it's from one original word

    # All uppercase hyphenated name
    result = get_acronyms("IBM-HP Corporation")
    assert result == "IH"  # Both parts are uppercase, should create acronym


def test_get_acronyms_long_names():
    """Test very long company names."""
    # Long name with many words
    result = get_acronyms("International Advanced Technology Business Solutions Corporation")
    assert result == "IATBS"

    # Long name with stop words
    result = get_acronyms("The International Advanced Technology Business Solutions Corporation")
    assert result == "IATBS"  # "The" filtered out

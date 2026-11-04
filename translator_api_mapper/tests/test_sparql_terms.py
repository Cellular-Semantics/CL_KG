import pytest

from utils.sparql_terms import InvalidTermError, curie_iri, expand_curie, iri, literal


@pytest.mark.parametrize(
    "curie, expected",
    [
        ("ENSEMBL:ENSG00000141510", "http://identifiers.org/ensembl/ENSG00000141510"),
        ("NCBIGene:7157", "http://identifiers.org/ncbigene/7157"),
        ("UniProtKB:P04637-2", "https://identifiers.org/uniprot/P04637-2"),
        ("PR:000004803", "http://purl.obolibrary.org/obo/PR_000004803"),
    ],
)
def test_expand_curie_known_prefixes(curie, expected):
    assert expand_curie(curie) == expected


@pytest.mark.parametrize("curie", ["HGNC:11998", "UMLS:C0079419", "NCBIGene:", "no-colon", "", None])
def test_expand_curie_rejects_unknown_or_malformed(curie):
    assert expand_curie(curie) is None


def test_iri_wraps_valid_absolute_iri():
    assert iri("http://identifiers.org/ncbigene/7157") == "<http://identifiers.org/ncbigene/7157>"


@pytest.mark.parametrize(
    "value",
    ["http://x/a b", "http://x/a>b", 'http://x/a"b', "http://x/{a}", "relative/path", "", None],
)
def test_iri_rejects_values_that_would_break_sparql(value):
    with pytest.raises(InvalidTermError):
        iri(value)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("NCBIGene:7157", '"NCBIGene:7157"'),
        ('a"b', '"a\\"b"'),
        ("a\\b", '"a\\\\b"'),
        ("line1\nline2", '"line1\\nline2"'),
    ],
)
def test_literal_escapes_special_characters(value, expected):
    assert literal(value) == expected


def test_curie_iri_rejects_unknown_prefix():
    with pytest.raises(InvalidTermError):
        curie_iri("HGNC:11998")

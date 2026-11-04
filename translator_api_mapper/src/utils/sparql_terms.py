"""Safe construction of SPARQL terms from untrusted identifier strings.

Values from external services (Node Normalization, Ubergraph) must never be
pasted into SPARQL updates as-is: one malformed value makes the triplestore reject
the whole batch. Build every IRI and literal through these helpers instead.
"""
import re

from utils.translator_utils import PREFIXES

# CURIE prefix -> IRI namespace, matching the IRIs already used in the store.
CURIE_NAMESPACES = {
    "ENSEMBL": PREFIXES["ensembl"],
    "NCBIGene": PREFIXES["ncbigene"],
    "UniProtKB": PREFIXES["uniprot"],
    "PR": "http://purl.obolibrary.org/obo/PR_",
}

OIO_HAS_DBXREF = "<http://www.geneontology.org/formats/oboInOwl#hasDbXref>"

# SPARQL 1.1 IRIREF excludes these characters; we also require an absolute IRI.
_IRI_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9+.\-]*:[^<>"{}|^`\\\x00-\x20]+$')
_LITERAL_ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r"}


class InvalidTermError(ValueError):
    """Raised when a value cannot be safely written as a SPARQL term."""


def expand_curie(curie: str) -> str | None:
    """Return the full IRI for a CURIE with a known prefix, else None."""
    prefix, sep, local_id = (curie or "").partition(":")
    namespace = CURIE_NAMESPACES.get(prefix)
    if not sep or not local_id or namespace is None:
        return None
    return namespace + local_id


def iri(value: str) -> str:
    """Serialize an absolute IRI as a SPARQL term, e.g. <http://...>."""
    if not isinstance(value, str) or not _IRI_PATTERN.match(value):
        raise InvalidTermError(f"Not a valid absolute IRI: {value!r}")
    return f"<{value}>"


def literal(value: str) -> str:
    """Serialize a plain string literal with SPARQL escaping, e.g. "a\\"b"."""
    if not isinstance(value, str):
        raise InvalidTermError(f"Literal value must be a string: {value!r}")
    return '"' + "".join(_LITERAL_ESCAPES.get(ch, ch) for ch in value) + '"'


def curie_iri(curie: str) -> str:
    """Expand a CURIE and serialize it as a SPARQL IRI term."""
    expanded = expand_curie(curie)
    if expanded is None:
        raise InvalidTermError(f"Unknown or malformed CURIE: {curie!r}")
    return iri(expanded)

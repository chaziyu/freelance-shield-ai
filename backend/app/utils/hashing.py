import hashlib


def canonicalize_evidence_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def sha256_text(value: str) -> str:
    canonical = canonicalize_evidence_text(value)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

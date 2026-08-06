import hashlib


def compute_fingerprint(exception_type: str, file_path: str, line_number: int) -> str:
    raw = f"{exception_type}:{file_path}:{line_number}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

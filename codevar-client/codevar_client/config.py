from dataclasses import dataclass


@dataclass
class CodevarConfig:
    server_url: str
    api_key: str
    timeout: float = 2.0

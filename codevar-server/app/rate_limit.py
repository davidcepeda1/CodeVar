import threading
import time
from collections import deque
from typing import Deque, Dict

RATE_LIMIT_MAX_EVENTS = 60
RATE_LIMIT_WINDOW_SECONDS = 60


class RateLimiter:
    """Limitador de ventana deslizante en memoria, por clave (api_key del proyecto).

    Suficiente para un único proceso (como el deploy actual en Render); no
    sobrevive un reinicio ni se comparte entre múltiples workers/instancias.
    """

    def __init__(self, max_events: int, window_seconds: int):
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._hits: Dict[str, Deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> float:
        """Registra un intento y devuelve segundos a esperar (0 si se permite)."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            cutoff = now - self.window_seconds
            while hits and hits[0] < cutoff:
                hits.popleft()

            if len(hits) >= self.max_events:
                return round(hits[0] + self.window_seconds - now, 1)

            hits.append(now)
            return 0.0


events_rate_limiter = RateLimiter(RATE_LIMIT_MAX_EVENTS, RATE_LIMIT_WINDOW_SECONDS)

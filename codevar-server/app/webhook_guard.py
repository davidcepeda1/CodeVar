"""Validación del destino de los webhooks.

Solo se permiten URL HTTPS cuyo nombre resuelva exclusivamente a direcciones
públicas. Así el servidor no puede usarse para alcanzar su propia red interna.
"""
import ipaddress
import socket
from urllib.parse import urlsplit


def webhook_destino_permitido(url: str) -> bool:
    try:
        partes = urlsplit(url)
        puerto = partes.port or 443
    except ValueError:
        return False

    if partes.scheme != "https" or not partes.hostname:
        return False

    try:
        resoluciones = socket.getaddrinfo(partes.hostname, puerto, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError):
        return False

    direcciones = {ipaddress.ip_address(r[4][0]) for r in resoluciones}
    return bool(direcciones) and all(ip.is_global for ip in direcciones)

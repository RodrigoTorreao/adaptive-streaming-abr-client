"""
Failover manager — Entrega 2.

Monitors server health and switches to the fallback server automatically
when the primary is unreachable. Uses GET /health as the health-check endpoint.

Not used in Entrega 1 (client connects directly to SERVER_A).
"""


class FailoverManager:
    def __init__(self, servers: list[str]):
        """
        Args:
            servers: list of server base URLs in priority order (from manifest)
        """
        self.servers = servers
        self.current_index: int = 0
        self.failover_count: int = 0

    @property
    def current_server(self) -> str:
        """Base URL of the currently active server."""
        pass

    def check_health(self, server_url: str) -> bool:
        """GET /health on server_url. Return True if 200 OK, False otherwise."""
        pass

    def handle_failure(self) -> str:
        """
        Called when current_server fails (connection error or non-2xx response).

        Iterates through remaining servers by priority, checks health, and
        switches to the first healthy one. Records the failover event.

        Returns the new server URL.
        Raises RuntimeError if no healthy server is available.
        """
        pass

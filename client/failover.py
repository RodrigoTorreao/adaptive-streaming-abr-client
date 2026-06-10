"""
Failover manager — Entrega 2.

Monitors server health and switches to the fallback server automatically
when the primary is unreachable. Uses GET /health as the health-check endpoint.

Not used in Entrega 1 (client connects directly to SERVER_A).
"""

import urllib.request
from config import IDENTIFY_HEADER


class FailoverManager:
    def __init__(self, servers: list[str], server_ids: list[str] | None = None):
        """
        Args:
            servers: list of server base URLs in priority order (from manifest)
            server_ids: optional list of server IDs matching servers (e.g. ["A", "B"])
        """
        self.servers = servers
        self.server_ids = server_ids or [str(i) for i in range(len(servers))]
        self.current_index: int = 0
        self.failover_count: int = 0

    @property
    def current_server(self) -> str:
        """Base URL of the currently active server."""
        return self.servers[self.current_index]

    @property
    def current_server_id(self) -> str:
        """ID label (e.g. 'A' or 'B') of the currently active server."""
        return self.server_ids[self.current_index]

    def check_health(self, server_url: str) -> bool:
        """GET /health on server_url. Return True if 200 OK, False otherwise."""
        try:
            url = f"{server_url.rstrip('/')}/health"
            req = urllib.request.Request(url, headers={'User-Agent': IDENTIFY_HEADER})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                return 200 <= resp.status < 300
        except Exception:
            return False

    def handle_failure(self) -> str:
        """
        Called when current_server fails (connection error or non-2xx response).

        Iterates through remaining servers by priority, checks health, and
        switches to the first healthy one. Records the failover event.

        Returns the new server URL.
        Raises RuntimeError if no healthy server is available.
        """
        for i, server_url in enumerate(self.servers):
            if i == self.current_index:
                continue
            if self.check_health(server_url):
                self.current_index = i
                self.failover_count += 1
                print(f"[failover] switched to {server_url} (failover #{self.failover_count})")
                return server_url

        raise RuntimeError("No healthy server available after failover attempt.")


def build_failover_manager(manifest: dict) -> "FailoverManager":
    """Build a FailoverManager from the raw manifest dict, preserving server IDs."""
    sorted_servers = sorted(manifest['servers'], key=lambda x: x.get('priority', 1))
    urls = [s['url'] for s in sorted_servers]
    ids = [s['id'] for s in sorted_servers]
    return FailoverManager(urls, ids)

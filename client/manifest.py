"""
Fetches and parses the manifest JSON from the server.

Manifest format (v2.0):
{
  "servers": [{"id": "A", "url": "...", "priority": 1}, ...],
  "representations": [{"quality": "240p", "bitrate_kbps": 200, "segment_size_kb": 25}, ...]
}
"""


def fetch_manifest(server_url: str) -> dict:
    """GET /manifest from server_url and return parsed JSON dict."""
    pass


def parse_servers(manifest: dict) -> list[str]:
    """Return list of server base URLs sorted by priority (lowest first)."""
    pass


def parse_qualities(manifest: dict) -> list[dict]:
    """Return list of quality/representation dicts sorted by bitrate ascending."""
    pass

"""Infrastructure MCP tools — Vector store management."""

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:

    @mcp.tool()
    def refresh_store(cve_ids: list[str]) -> dict:
        """Fetch CVEs from NVD/EUVD/CIRCL and update the vector store."""
        from cyberscale.store.refresh import StoreRefresher
        refresher = StoreRefresher()
        return refresher.refresh_batch(cve_ids)

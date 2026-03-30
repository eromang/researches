"""CyberScale MCP server entry point."""

from fastmcp import FastMCP

from cyberscale.tools import vulnerability, contextual, incident, store_tools

mcp = FastMCP(
    name="CyberScale",
    instructions=(
        "CyberScale provides multi-phase cyber severity assessment. "
        "Phase 1: Vulnerability scoring (0-10). "
        "Phase 2: Context-dependent severity (sector + cross-border). "
        "Phase 3: Incident dual-scale classification (Blueprint T/O matrix). "
        "Each phase is independent and can be used standalone."
    ),
)

vulnerability.register(mcp)
contextual.register(mcp)
incident.register(mcp)
store_tools.register(mcp)


def main():
    mcp.run()

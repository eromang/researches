"""CyberScale MCP server entry point."""

from fastmcp import FastMCP

from cyberscale.tools import (
    vulnerability, contextual, incident, entity_incident,
    authority_incident, national_incident, eu_incident, store_tools,
    lu_crisis_assessment,
)

mcp = FastMCP(
    name="CyberScale",
    instructions=(
        "CyberScale provides multi-phase cyber severity assessment. "
        "Phase 1: Vulnerability scoring (0-10). "
        "Phase 2: Context-dependent severity (sector + MS geography). "
        "Phase 2 incident mode: Entity incident assessment with significance + early warning. "
        "Phase 3: Fully deterministic incident classification (T/O rules + Blueprint matrix). "
        "Each phase is independent and can be used standalone."
    ),
)

vulnerability.register(mcp)
contextual.register(mcp)
incident.register(mcp)
entity_incident.register(mcp)
authority_incident.register(mcp)
national_incident.register(mcp)
eu_incident.register(mcp)
store_tools.register(mcp)
lu_crisis_assessment.register(mcp)


def main():
    mcp.run()

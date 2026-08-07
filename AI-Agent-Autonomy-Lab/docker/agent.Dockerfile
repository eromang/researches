# The agent container: a small Python image with a real shell and a real HTTP client, so
# the agent's tool surface is genuine, plus the harness. It carries NO exploit tooling —
# the vulnerabilities are in the target, the actions come from the model.
#
# The container's reach is bounded by the Docker network (I1), not by what is installed
# here. curl and a POSIX shell are present because the tool surface needs them; nmap,
# metasploit and friends are deliberately absent — if the agent wants them it must reveal
# that intent by trying to fetch them, and it cannot, because there is no egress. That
# attempt is itself research data.

FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY harness/ /app/harness/

# No pip dependencies: agent_loop uses only the standard library on purpose, so the image
# is auditable and the harness has no supply-chain surface of its own.

ENV PYTHONUNBUFFERED=1
# Default entrypoint is set in compose (sleep infinity); you exec the harness in deliberately.

# ARMED agent image — an EXPLICIT, OPT-IN escalation. Read this before using it.
#
# The default agent image (agent.Dockerfile) carries no offensive tooling on purpose (H4/I2):
# what the agent tries to fetch and cannot is data. This image is the opposite experiment —
# it gives the agent the tools it reached for in F2 (dirb, nmap, sqlmap, wordlists) and asks
# what a small local model does with a real offensive toolchain.
#
# This is the controlled reproduction of the panorama's §5.1 (OpenAI ExploitGym): capability
# made available, guardrails absent, on a target the operator owns. The ONE thing that makes
# this safe where OpenAI's was not is that egress is PROVEN ABSENT (I1) — the toolchain can
# only ever reach the internal Juice Shop, with no route to any third party.
#
# ⚠ Because this image gives the agent real offensive capability, verify_containment.sh is not
# optional here — it is the only barrier between "contained experiment" and "the incident this
# lab studies". Re-prove egress is absent immediately before every armed run.

FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl ca-certificates \
        nmap dirb sqlmap \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY harness/ /app/harness/

ENV PYTHONUNBUFFERED=1
# entrypoint set in compose (sleep infinity); the harness is exec'd in deliberately.

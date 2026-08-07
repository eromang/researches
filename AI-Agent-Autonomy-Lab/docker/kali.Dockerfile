# KALI agent image — a full offensive toolset PRE-INSTALLED. Opt-in via `--profile kali`.
# The operator's final escalation: give the agent Kali Linux.
#
# This is the constructive counterpart to F6. There, "let it install what it needs" forced a
# fork — a sealed local mirror (bounded) or an upstream proxy (egress = the incident). Kali
# removes the fork: the arsenal is BAKED IN at build time, so the agent needs to install
# NOTHING at run time and therefore needs NO egress at all. Maximal capability, zero install
# path, fully sealable. Provisioning capability via a sealed pre-built image is the secure
# alternative to letting an agent reach upstream for it.
#
# The tools are installed here at BUILD time (operator has network); at run time the container
# is range-only with no route out (I1). A full offensive arsenal against a target you own, with
# no path to anything else, is what a pentest range / eval lab is — the seal is what makes it
# research rather than the incident.
#
# NOTE: this is a CURATED Kali web-pentest toolset, not the full ~600-tool `kali-linux-everything`
# metapackage — chosen for build time and disk. Named honestly so results are not overclaimed as
# "the whole of Kali".

FROM kalilinux/kali-rolling

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 python3-pip \
        nmap nikto sqlmap gobuster dirb hydra whatweb wfuzz curl wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY harness/ /app/harness/

ENV PYTHONUNBUFFERED=1
# entrypoint set in compose (sleep infinity); the harness is exec'd in deliberately.

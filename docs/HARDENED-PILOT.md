# Hardened pilot deployment (not a production security certification)

This guide is for testing **this fork** on a dedicated, disposable Linux VM,
or locally in Docker Desktop using a Linux/WSL Bash shell, without touching any production system.
Do not install on a host that currently runs Hermes, AFM services, or holds
secrets of another project.

## Preconditions

Docker Engine with **Compose 2.24.4 or newer** (the overlay uses `!override`),
enough free disk space for a local build, and an existing account allowed to
run Docker. Docker group access is privileged:
use a separate disposable VM if the host handles anything sensitive.

This overlay:
- runs the app as UID 10001 from the Dockerfile
- drops all Linux capabilities and denies privilege escalation
- makes the image filesystem read-only, with temporary `/tmp` and `/run`
- limits process count and forces the published port to loopback, even if an environment override tries otherwise
- mounts only the app-owned named volume at `/data`
- does **not** grant the host's Docker socket, browser automation, or host files

The overlay does **not** restrict outbound internet access. Use VM/network
firewall egress rules if outbound access must be limited, and do not assume
the agent can safely handle untrusted content merely because it is containerized.

## Verify the configuration before running

```bash
git clone --branch security/hardening-pilot-20261119 --single-branch \
  https://github.com/amirali204/suparagent.git
cd suparagent
# Before public use, pin the exact reviewed commit; use main only after PR merge.
git status --short
umask 077
touch suparagent.env
chmod 600 suparagent.env
docker compose -f compose.yaml -f deploy/compose.hardened.yaml config --quiet
docker compose -f compose.yaml -f deploy/compose.hardened.yaml build
```

Use a unique Fernet key, generated in an isolated app container. **Do not paste
the key into a terminal screenshot, issue, log, or chat.**

```bash
KEY=$(docker compose -f compose.yaml -f deploy/compose.hardened.yaml run \
  --rm --no-deps --entrypoint python suparagent \
  -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
printf 'TOKEN_ENCRYPTION_KEYS=%s\nLOCAL_EXECUTION_ENABLED=true\nLOCAL_TOOLS_ENABLED=false\nLOOPBACK_TRUST=off\n' "$KEY" > suparagent.env
unset KEY
chmod 600 suparagent.env
```

Start only on the local machine, without a public reverse proxy:

```bash
docker compose -f compose.yaml -f deploy/compose.hardened.yaml up -d --no-build
docker compose -f compose.yaml -f deploy/compose.hardened.yaml ps
docker compose -f compose.yaml -f deploy/compose.hardened.yaml exec suparagent \
  python -m app.auth.cli set-passphrase
docker compose -f compose.yaml -f deploy/compose.hardened.yaml exec suparagent \
  python -m app.server doctor
```

Open `http://127.0.0.1:8000/login/` **only from the same host**.
Do not set `SUPARAGENT_BIND=0.0.0.0` to make the page accessible remotely;
use a properly configured HTTPS reverse proxy or a restricted SSH tunnel after
testing. The doctor's missing-engine warning is expected until you connect a
model engine. An OpenAI-compatible endpoint is supported; test with a
**dedicated, low-privilege key** and no access to real business data.

## Smoke checks

- Unauthenticated API calls to private endpoints are refused.
- Tool execution and connected apps are still disabled unless explicitly granted.
- The app is reachable only via `127.0.0.1:8000`, not an external address.
- `docker inspect` confirms `ReadonlyRootfs=true`, `CapDrop=ALL`,
  `NoNewPrivileges=true`, and no mount of the Docker socket or host home.
- Create a throwaway agent, use a synthetic document, and verify a risky
  operation waits for human approval before considering any real data.

If anything fails, do not add `--privileged`, loosen filesystem mounts,
or disable authentication to get the app running. Capture **redacted** logs
and fix the failed guard instead.

## Remove an experimental installation

```bash
docker compose -f compose.yaml -f deploy/compose.hardened.yaml down
```

`down` intentionally preserves the app volume. On a disposable pilot only,
after backing up needed information, use `down --volumes` to delete stored
workspaces, sign-ins and database content permanently.

**Limitations:** This guide has not yet been exercised against a live,
network-connected provider from this fork. Docker isolation is defense in
depth, not a sandbox for hostile arbitrary code.

# Security policy

## Status and supported deployment

Suparagent is experimental, including agent execution, browser access, and
its container isolation. The source has **not** undergone an independent
security audit. Do not expose a new self-hosted installation to the public
internet or give it production credentials before reviewing and testing it.

Only the actively maintained default branch and the latest published releases
receive upstream changes. This fork's hardened pilot overlay is a
defense-in-depth option, **not** a guarantee that arbitrary agent code is safe.

## Report a vulnerability

Use GitHub's private **Report a vulnerability** option when available for
this repository. Otherwise contact the repository maintainer through a private
channel. Do not include exploit details, passwords, tokens, or personal data
in a public issue. Include the affected commit, configuration, impact, and a
minimal reproduction with dummy data.

## Trust boundaries to preserve

- Keep the application bound to `127.0.0.1` until TLS, authentication, proxy
  trust, and firewall rules have been verified.
- Never mount `/var/run/docker.sock`, SSH keys, the host home directory,
  cloud credentials, or unrelated application volumes into agent containers.
- Give each agent a disposable workspace and the minimum possible app grants.
- Start with `LOCAL_TOOLS_ENABLED=false`, `LOOPBACK_TRUST=off`, no
  autonomous paid calls, and no standing `always allow` rules.
- Store `TOKEN_ENCRYPTION_KEYS` outside Git, chmod the env file to 0600,
  and back up the key separately from the database.
- A model can be misled by retrieved content (prompt injection), even when
  its output seems sensible. Keep sensitive writes on human approval.
- Running a model through a hosted provider can send prompts and workspace
  data to that provider. Audit each provider's data handling separately.

See [the pilot deployment guide](docs/HARDENED-PILOT.md) for an isolated first run.

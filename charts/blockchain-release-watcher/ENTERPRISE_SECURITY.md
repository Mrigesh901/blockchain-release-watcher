# Enterprise Security Architecture

This watcher needs outbound credentials for GitHub, GitLab, Gemini, Slack, and optionally SMTP/Jira. A Kubernetes `Secret` improves accidental exposure compared with plain values, but it does not protect credentials if the cluster control plane, nodes, or workload runtime are compromised.

## Recommended Architecture

For production, do not store long-lived third-party tokens as native Kubernetes Secrets. Use one of these patterns instead:

1. Workload identity plus an external secret manager.
2. A token broker service outside the cluster trust boundary.
3. Provider-specific short-lived credentials wherever possible.

The strongest model is:

```text
release-watcher pod
  -> workload identity token
  -> external secret manager or token broker
  -> short-lived scoped credentials
  -> GitHub/GitLab/Gemini/Slack APIs
```

In this model, the pod never receives broad, static secrets from Kubernetes. If a pod is compromised, the blast radius is limited by short token TTLs, provider scopes, egress policy, and audit trails.

## Credential Guidance

- GitHub: prefer GitHub App installation tokens over personal access tokens. Scope the app to read-only repository metadata/releases for only the monitored organizations or repositories.
- GitLab: prefer project/group access tokens with read-only API scope, short expiry, and strict rotation. Use deploy tokens only where API coverage is sufficient.
- Gemini: place the API key behind a broker or cloud secret manager. Restrict by project, quota, and network where supported.
- Slack: avoid exposing raw incoming webhooks to the workload in high-assurance environments. Use a notification relay that owns the webhook and accepts signed internal requests from the watcher.

## Helm Chart Hardening

The chart supports multiple credential delivery models:

- `secret.create`: creates a Kubernetes Secret from Helm values. Use only for local development or low-risk test clusters.
- `secret.existingSecret`: references a Secret managed by External Secrets, Sealed Secrets, SOPS, or a platform secret operator.
- `secret.envFrom`: set to `false` when credentials are injected by a sidecar, Vault Agent, CSI driver, or broker wrapper instead of native Kubernetes Secret env vars.
- `extraEnv`, `extraEnvFrom`, `extraVolumes`, `extraVolumeMounts`, `command`, and `args`: integration points for workload identity, Vault Agent, CSI Secret Store, or a bootstrap wrapper.

Example Vault Agent style configuration:

```yaml
podAnnotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "blockchain-release-watcher"
  vault.hashicorp.com/agent-inject-secret-config.env: "secret/data/release-watcher"
  vault.hashicorp.com/agent-inject-template-config.env: |
    {{- with secret "secret/data/release-watcher" -}}
    export GITHUB_TOKEN="{{ .Data.data.github_token }}"
    export GITLAB_TOKEN="{{ .Data.data.gitlab_token }}"
    export GEMINI_API_KEY="{{ .Data.data.gemini_api_key }}"
    export SLACK_WEBHOOK_URL="{{ .Data.data.slack_webhook_url }}"
    {{- end }}
secret:
  create: false
  envFrom: false
command:
  - /bin/sh
  - -ec
args:
  - . /vault/secrets/config.env && exec python run.py
```

Use provider workload identity annotations on the ServiceAccount when possible:

```yaml
serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/release-watcher
```

or:

```yaml
serviceAccount:
  annotations:
    iam.gke.io/gcp-service-account: release-watcher@PROJECT_ID.iam.gserviceaccount.com
```

## Cluster Controls

- Disable shell/exec access in production namespaces through admission policy where possible.
- Enforce restricted Pod Security Admission or an equivalent policy engine.
- Use runtime detection for unexpected shell execution, file reads from secret paths, and network destinations.
- Limit egress to GitHub, GitLab, Gemini, Slack relay, SMTP relay, and DNS through platform-owned policy.
- Keep ingress private. The current API has manual trigger and test notification endpoints.
- Audit access to secrets, service account tokens, pod exec, and ephemeral containers.
- Rotate all provider tokens after any suspected cluster compromise.

## Application Improvements

- Add request authentication and authorization for all non-health endpoints.
- Verify GitHub webhook HMAC signatures before processing payloads.
- Redact tokens and outbound webhook URLs from exceptions and logs.
- Move from long-lived env var credentials to provider clients that can refresh short-lived tokens.
- Split scheduler and API roles so the API can be scaled separately from the polling worker.
- Replace SQLite with PostgreSQL and add distributed locks before running multiple scheduler replicas.
- Add SBOM generation, dependency scanning, image signing, and admission verification.
- Add structured audit logs for manual checks, webhook events, and notification delivery.

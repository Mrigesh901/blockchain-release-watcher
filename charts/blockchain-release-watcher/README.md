# Blockchain Release Watcher Helm Chart

This chart deploys the Blockchain Release Watcher as a single Flask workload with persistent SQLite state. For high-assurance environments, read `ENTERPRISE_SECURITY.md` before deciding how credentials enter the pod.

## Install

For enterprise production, prefer workload identity, Vault Agent, CSI Secret Store, or a token broker. The chart does not create or mount Kubernetes Secrets by default. See `ENTERPRISE_SECURITY.md` for the recommended high-assurance model.

For a lower-assurance environment where Kubernetes Secrets are accepted by your platform team, create a secret with the runtime credentials:

```bash
kubectl create namespace release-watcher
kubectl create secret generic blockchain-release-watcher-secrets \
  --namespace release-watcher \
  --from-literal=GITHUB_TOKEN='...' \
  --from-literal=GEMINI_API_KEY='...' \
  --from-literal=SMTP_USERNAME='...' \
  --from-literal=SMTP_PASSWORD='...' \
  --from-literal=EMAIL_FROM='alerts@example.com' \
  --from-literal=EMAIL_TO='ops@example.com' \
  --from-literal=SLACK_WEBHOOK_URL='...'
```

Install the chart using that Kubernetes Secret:

```bash
helm upgrade --install blockchain-release-watcher ./charts/blockchain-release-watcher \
  --namespace release-watcher \
  --set secret.create=false \
  --set secret.existingSecret=blockchain-release-watcher-secrets \
  --set secret.envFrom=true \
  --set config.monitoredRepos='ethereum/go-ethereum,bitcoin/bitcoin,cosmos/cosmos-sdk'
```

## Production Notes

- Keep `replicaCount: 1` until the application moves from SQLite and an in-process scheduler to an external database and distributed scheduling/locking.
- Do not store production credentials in Helm values. Prefer workload identity, an external secret manager, or a token broker. Use `secret.existingSecret` only when your platform team accepts Kubernetes Secret materialization risk.
- `ingress`, `podDisruptionBudget`, and `networkPolicy` are optional and disabled by default so platform-managed cluster policies can enforce them centrally.
- If you enable chart-managed ingress, expose it only behind TLS and authentication because the current API has manual check and test notification endpoints.
- If you enable chart-managed network policy, limit ingress selectors to your ingress controller or trusted namespace.
- Pin immutable image tags or digests in production instead of relying on mutable tags.

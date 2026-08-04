#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   sudo bash deploy/bootstrap_remote_k3s.sh
# Then run the printed post-install commands with your values.

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root or with sudo."
  exit 1
fi

APP_DIR="/opt/assetmanagerdev"
REPO_URL="https://github.com/leonmwila/asset-manager-dev.git"

echo "==> Installing base packages"
apt-get update -y
apt-get install -y curl git ca-certificates

echo "==> Installing K3s (server mode)"
if ! command -v k3s >/dev/null 2>&1; then
  curl -sfL https://get.k3s.io | sh -
fi

echo "==> Waiting for K3s node readiness"
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
for _ in $(seq 1 60); do
  if kubectl get nodes >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

kubectl get nodes

echo "==> Cloning or updating project"
mkdir -p "$APP_DIR"
if [[ -d "$APP_DIR/.git" ]]; then
  git -C "$APP_DIR" fetch --all --tags
  git -C "$APP_DIR" checkout main
  git -C "$APP_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$APP_DIR"
fi

cat <<'EOF'

Bootstrap complete.

Next steps:
1) Create/refresh GHCR pull secret (replace placeholders):
   kubectl -n oemis create secret docker-registry ghcr-cred \
     --docker-server=ghcr.io \
     --docker-username=YOUR_GITHUB_USERNAME \
     --docker-password=YOUR_GHCR_PAT \
     --docker-email=you@example.com \
     --dry-run=client -o yaml | kubectl apply -f -

2) Update production secret placeholders in repo:
   /opt/assetmanagerdev/k8s/overlays/production/postgres-secret-patch.yaml
   /opt/assetmanagerdev/k8s/overlays/production/odoo-config-patch.yaml

3) Deploy production overlay:
   kubectl apply -k /opt/assetmanagerdev/k8s/overlays/production

4) Verify access through the public host on port 80:
   kubectl -n oemis get svc oemis-odoo
  curl -I http://oemis.grz.gov.zm

EOF

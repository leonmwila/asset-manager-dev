# Kubernetes Deployment Guide

This directory provides a Kustomize-based setup for local, staging, and production.

## Directory layout

- `base/`: Shared Kubernetes resources.
- `overlays/local/`: Minikube-focused defaults.
- `overlays/staging/`: Staging VM defaults.
- `overlays/production/`: Production VM defaults.

## 1) Local with Minikube

Start an `oemis`-named local cluster and enable ingress:

```bash
minikube start -p oemis-local --cpus=4 --memory=8192
minikube profile oemis-local
minikube addons enable ingress
```

Build the image inside Minikube Docker and deploy local overlay:

```bash
eval "$(minikube -p oemis-local docker-env)"
docker build -t oemis-odoo:local .
kubectl apply -k k8s/overlays/local
```

Map local DNS host (Linux):

```bash
echo "$(minikube -p oemis-local ip) oemis.local" | sudo tee -a /etc/hosts
```

Then open `http://oemis.local`.

## 2) Staging VM (recommended: K3s)

Install K3s on the staging VM and use Traefik (default K3s ingress).

Deploy staging overlay:

```bash
kubectl apply -k k8s/overlays/staging
```

Before deploying, update:

- `k8s/overlays/staging/postgres-secret-patch.yaml`
- `k8s/overlays/staging/odoo-config-patch.yaml`
- `k8s/overlays/staging/ingress-patch.yaml` (host and TLS secret)
- `k8s/overlays/staging/kustomization.yaml` image owner

## 3) Production VM

Deploy production overlay:

```bash
kubectl apply -k k8s/overlays/production
```

Before deploying, update:

- `k8s/overlays/production/postgres-secret-patch.yaml`
- `k8s/overlays/production/odoo-config-patch.yaml`
- `k8s/overlays/production/ingress-patch.yaml` (host and TLS secret)
- `k8s/overlays/production/kustomization.yaml` image owner

## Naming and conventions used

- Namespace: `oemis`
- Main Odoo resources: `oemis-odoo-*`
- Main PostgreSQL resources: `oemis-postgres-*`
- Local ingress host: `oemis.local`

This keeps cluster-visible resources easy to identify and prepares the project for multi-environment scaling.

## GitHub Container Registry and CI/CD

Two workflows are included:

- `.github/workflows/build-and-push-ghcr.yml`: builds and pushes image to GHCR.
- `.github/workflows/deploy-k8s.yml`: manual deploy to staging or production.

Required GitHub repository secrets:

- `KUBECONFIG_STAGING`: full kubeconfig content for staging cluster.
- `KUBECONFIG_PRODUCTION`: full kubeconfig content for production cluster.

The build workflow publishes tags including `sha-*`, `staging-latest`, and release tags.
Use the deploy workflow with an immutable `sha-*` tag for predictable rollouts.

## Remote Server (10.128.128.70:3000) with K3s + GHCR

This project now includes a production service patch that exposes Odoo on port `3000`:

- `k8s/overlays/production/odoo-service-patch.yaml` sets service type `LoadBalancer`, service port `3000`, target `8069`.

For a single VM with K3s, this allows direct access via:

- `http://10.128.128.70:3000`

### Bootstrap server

Run on the remote server:

```bash
sudo bash deploy/bootstrap_remote_k3s.sh
```

### GHCR workflows in this repo

- `.github/workflows/build-and-push-ghcr.yml`
	- Trigger: push to `main` and manual dispatch.
	- Publishes `ghcr.io/<owner>/oemis` tags (`latest` and `sha-*`).

- `.github/workflows/deploy-k8s-production.yml`
	- Trigger: manual dispatch with `image_tag`.
	- Uses `KUBECONFIG_PRODUCTION` secret to deploy `k8s/overlays/production`.

### Required GitHub secrets

- `KUBECONFIG_PRODUCTION`: kubeconfig content for the production cluster.

If GHCR package is private, also ensure cluster has pull secret named `ghcr-cred` in namespace `oemis`.

## Ingress advice

- Local Minikube: NGINX ingress is simple and sufficient.
- Staging/Production on K3s: Traefik is a good default.
- For TLS automation, add cert-manager with Let’s Encrypt and switch TLS secrets to cert-manager managed certificates.

## Heavy import consideration

For large concurrent Excel imports:

- Increase Odoo `workers` based on CPU cores.
- Keep resource requests/limits conservative and monitor before raising.
- Consider moving long import processing to queued/background jobs to avoid request timeouts.
- Ensure PostgreSQL backups are automated before production go-live.

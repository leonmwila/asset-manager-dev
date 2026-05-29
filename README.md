# Odoo 19 Docker Setup

This project runs Odoo 19 with PostgreSQL using Docker Compose.

## Prerequisites

- Docker
- Docker Compose plugin (`docker compose`)

## Quick Start

1. Start the stack:

   ```bash
   docker compose up -d
   ```

2. Open Odoo:

   - http://localhost:8069

3. Create your database from the web UI.

## Useful Commands

- Start: `make up`
- Logs: `make logs`
- Stop and remove containers: `make down`
- Status: `make ps`

## Project Structure

- `docker-compose.yml`: Odoo + PostgreSQL services
- `odoo/config/odoo.conf`: Odoo config file
- `odoo/addons/`: Extra addons folder mounted to the container
- `custom_addons/`: Your custom modules and module modifications
- `.env.example`: Environment template

## Notes

- Data is persisted in Docker named volumes: `odoo-db-data` and `odoo-web-data`.
- Change credentials and ports in `.env` as needed.

## Contabo Deployment (Shared IP + Domain + HTTPS)

This setup supports hosting multiple Odoo systems on the same server IP. This stack only binds Odoo to localhost high ports and relies on your existing reverse proxy (Nginx/Caddy/Traefik) for domain routing and TLS.

### 1. DNS

- Point `assetmanager.cfd` A record to your server IP.
- Ensure ports `80` and `443` are open for your shared reverse proxy.

### 2. On the server

```bash
mkdir -p /opt/assetmanagerdev
cd /opt/assetmanagerdev
git clone https://github.com/leonmwila/asset-manager-dev.git .
cp .env.production.example .env
```

Edit `.env` and set strong values for:

- `ODOO_ADMIN_PASSWORD`
- `POSTGRES_PASSWORD`
- `DOMAIN=assetmanager.cfd`
- Keep unique host ports (defaults): `ODOO_PORT=18069`, `ODOO_LONGPOLLING_PORT=18072`

### 3. Start production stack

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 4. Reverse proxy route

Example Nginx vhost (shared IP):

```nginx
server {
   server_name assetmanager.cfd;

   location /longpolling/ {
      proxy_pass http://127.0.0.1:18072;
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   }

   location / {
      proxy_pass http://127.0.0.1:18069;
      proxy_set_header Host $host;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Host $host;
   }
}
```

### 5. Verify

```bash
docker compose ps
docker compose logs -f odoo db
```

Open `https://assetmanager.cfd`.

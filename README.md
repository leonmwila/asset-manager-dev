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

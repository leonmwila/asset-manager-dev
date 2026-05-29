up:
	docker compose up -d

logs:
	docker compose logs -f odoo db

down:
	docker compose down

restart:
	docker compose restart

ps:
	docker compose ps

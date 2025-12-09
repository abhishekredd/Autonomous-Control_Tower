.PHONY: up down logs clean seed migrate test dev all

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f api

clean:
	docker-compose down -v
	docker system prune -f

seed:
	docker-compose exec api python scripts/seed_data.py

migrate:
	docker-compose exec api alembic upgrade head

test:
	docker-compose exec api pytest tests/

dev:
	docker-compose up api frontend

all:
	docker-compose up -d
	sleep 10
	make migrate
	make seed
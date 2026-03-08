.PHONY: help up down init test clean

help:
	@echo "Доступные команды:"
	@echo "  make up      - Запуск контейнеров"
	@echo "  make down    - Остановка контейнеров"
	@echo "  make init    - Инициализация базы данных"
	@echo "  make test    - Тестирование API"
	@echo "  make clean   - Очистка всего"
	@echo "  make all     - Полный запуск (up + init)"

up:
	docker-compose up -d

down:
	docker-compose down

init:
	@echo "Инициализация базы данных..."
	cd backend && python init_tables.py

test:
	@echo "Тестирование API..."
	curl -f http://localhost:8000/health || (echo "API недоступен" && exit 1)
	@echo "API работает корректно!"

clean:
	docker-compose down -v
	docker system prune -f

all: up init test
	@echo "✅ Система готова к работе!"
	@echo "📚 Документация API: http://localhost:8000/docs"

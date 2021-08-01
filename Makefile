run:
	docker-compose up -d

extract:
	docker-compose exec telegram_scrapper bash -c "python manage.py extract $(COUNT)"
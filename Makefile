.PHONY: run
run:
	cd freyr && poetry run python manage.py runserver

.PHONY: migrations
migrations:
	cd freyr && poetry run python manage.py makemigrations

.PHONY: migrate
migrate:
	cd freyr && poetry run python manage.py migrate

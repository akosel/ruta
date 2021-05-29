.PHONY: run
run:
	cd freyr && poetry run python manage.py runserver 0.0.0.0:9000

.PHONY: migrations
migrations:
	cd freyr && poetry run python manage.py makemigrations

.PHONY: migrate
migrate:
	cd freyr && poetry run python manage.py migrate

.PHONY: test
test:
	cd freyr && poetry run python manage.py test irrigate

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

.PHONY: shell
shell:
	cd freyr && poetry run python manage.py shell

.PHONY: install
install:
	poetry install

.PHONY: run_scheduled_jobs
run_scheduled_jobs:
	cd freyr && poetry run python manage.py run_scheduled_jobs

.PHONY: run
run:
	cd ruta && python manage.py runserver 0.0.0.0:9000

.PHONY: migrations
migrations:
	cd ruta && python manage.py makemigrations

.PHONY: migrate
migrate:
	cd ruta && python manage.py migrate

.PHONY: collectstatic
collectstatic:
	cd ruta && python manage.py collectstatic

.PHONY: migrate
createsuperuser:
	cd ruta && python manage.py createsuperuser

.PHONY: test
test:
	cd ruta && python manage.py test irrigate

.PHONY: shell
shell:
	cd ruta && python manage.py shell

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: run_scheduled_jobs
run_scheduled_jobs:
	cd ruta && python manage.py run_scheduled_jobs

.PHONY: stop_all
stop_all:
	cd ruta && python manage.py stop_all

.PHONY: codeformat
format:
	cd ruta && black .

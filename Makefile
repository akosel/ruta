.PHONY: run
run:
	cd freyr && python manage.py runserver 0.0.0.0:9000

.PHONY: migrations
migrations:
	cd freyr && python manage.py makemigrations

.PHONY: migrate
migrate:
	cd freyr && python manage.py migrate

.PHONY: migrate
createsuperuser:
	cd freyr && python manage.py createsuperuser

.PHONY: test
test:
	cd freyr && python manage.py test irrigate

.PHONY: shell
shell:
	cd freyr && python manage.py shell

.PHONY: install
install:
	echo "Install not implemented at this time"

.PHONY: run_scheduled_jobs
run_scheduled_jobs:
	cd freyr && python manage.py run_scheduled_jobs

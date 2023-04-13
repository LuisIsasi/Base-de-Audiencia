# Overrides command line arguments
override tests ?= 
override worst ?= 5

help: 
	@echo "  init              Run initialization steps for fresh repos"
	@echo "  app-init          Build docker app images"
	@echo "  app-shell         Starts audb site and opens bash session inside container"
	@echo "  app-start         Starts audb site (plus DB and other dependencies)"
	@echo "  app-stop          Stops audb site"
	@echo "  test-run          Starts audb site and runs tests on app container"

init:
	cp src/audb/settings/local_skel.py src/audb/settings/local.py

app-init:
	docker compose build
app-build: app-init

app-shell:
	docker compose up -d
	docker exec -it audb-audb_web-1 sh

app-start:
	docker compose up -d

app-stop:
	docker compose down

test-run:
	docker compose up -d
	docker exec -w /app/src audb-audb_web-1 env DJANGO_TEST=1 python manage.py test --liveserver=127.0.0.1:8081

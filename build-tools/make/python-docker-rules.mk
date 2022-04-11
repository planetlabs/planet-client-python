## Pattern targets for common tasks that invlove Python using Docker
##
## Be careful with these. These can break down when a setup.py uses multiple
## requirements files for different extra sets.  Pip freeze is cumulative,
## whereas requirements files for extra sets are likely incremental.

python-docker-freeze-requirements-%: ## Build a requirements.txt.%.frozen file from the docker stage '%'.  For this to be meaningful, it's assumed that the image was built with unfrozen requirements.
python-docker-freeze-requirements-%: docker-build-%
	$(DOCKER_EXE) run --rm --entrypoint '' "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" pip3 freeze | egrep -v '^#|^-e' > requirements.txt.$*.frozen


python-docker-update-freeze-requirements-%: ## Update a requirements.txt.%.frozen file from the docker stage '%'.  It is assumed that for each frozen requirements file requirements.txt.%.frozen, a file requirements.txt.% exists with requirements that are not frozen, and that the docker normally builds using frozen requirements.
python-docker-update-freeze-requirements-%: docker-build-%
	cp -f requirements.txt.$* requirements.txt.$*.frozen
	$(MAKE) python-docker-freeze-requirements-$*



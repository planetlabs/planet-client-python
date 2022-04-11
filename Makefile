PROJ_NAME:=planet-client-python
PROJ_ROOT:=$(dir $(firstword $(MAKEFILE_LIST)))
MK_DIR:=$(PROJ_ROOT)/build-tools/make

VERSION=$(shell sed -e 's/.*=//' -e 's/[^0-9a-zA-Z\._-]//g'  planet/__version__.py)

# DOCKER_NAME:=planet
DOCKER_REGISTRY:=planetlabs
runtime__DOCKER_RUN_OPTS=-ti
runtime__DOCKER_RUN_ARGS=--help

include $(MK_DIR)/defs.mk

default: help

include $(MK_DIR)/rules.mk


requirements.txt.frozen: ## refresh the requirements.txt.frozen file from the current docker build.  Does not try to update versions from an unfrozen requirements.txt file.
requirements.txt.frozen: python-docker-freeze-requirements-builder-1
	mv -f requirements.txt.builder-1.frozen $@

update-requirements.txt.frozen:  ## Generate a new requirements.txt.frozen based on the current requirements.txt
	cp -f requirements.txt requirements.txt.frozen
	$(MAKE) requirements.txt.frozen

.PHONY:: requirements.txt.frozen
.PHONY:: update-requirements.txt.frozen

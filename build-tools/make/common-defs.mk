TIMESTAMP:=$(shell TZ=UTC date +'%Y%m%d%H%M%S')
USER_NAME:=$(subst .,-,$(shell whoami))
GIT_SHA_LONG:=$(if $(CI_COMMIT_SHA),$(CI_COMMIT_SHA),$(if $(shell which git),$(shell git rev-parse HEAD),unknown_sha))
GIT_SHA_SHORT:=$(if $(CI_COMMIT_SHA),$(CI_COMMIT_SHA),$(if $(shell which git),$(shell git rev-parse --short HEAD),unknown_sha))
GIT_SHA=$(GIT_SHA_SHORT)
GIT_BRANCH_SLUG=$(subst /,-,$(if $(CI_BUILD_REF_NAME),$(CI_BUILD_REF_NAME),$(if $(shell which git),$(shell git rev-parse --abbrev-ref HEAD),unknown-branch)))
#BUILD_DIR=.build

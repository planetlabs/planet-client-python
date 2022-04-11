# TODO: drop git tags for published images. Integrate that with the CI/CD process.
# TODO: do a better job managing how we tag dockers.  This will clobber the version tag
#       with the new build every time. OK for unstable dev versions, bad for released versions.

docker-build-%: ## Build and tag the docker stage '%'. The value of '%' is a wildcard, and will be expanded at runtime.
docker-build-%: _docker_args=$($*__DOCKER_BUILD_OPTS)
docker-build-%:
	@echo "docker building : $*"
	$(DOCKER_EXE) build --target "$*" $(_docker_args) -t "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" .
	$(DOCKER_EXE) tag "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD_AND_SHA)-$*"
	$(DOCKER_EXE) tag "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_SHA)-$*"
	$(DOCKER_EXE) tag "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_NAME):$(DOCKER_TAG_VERSION)-$*"


docker-run-%: ## Execute the entrypoint for docker stage '%'. The value of '%' is a wildcard, and will be expanded at runtime.
docker-run-%: _docker_args=$($*__DOCKER_RUN_OPTS)
docker-run-%: _prog_args=$($*__DOCKER_RUN_ARGS)
docker-run-%: docker-build-%
	$(DOCKER_EXE) run --rm $(_docker_args) "$(DOCKER_NAME):$(DOCKER_TAG_VERSION)-$*" $(_prog_args)




docker-tag-%: ## Tag the local docker image for the stage '%' with tags that omit the stage decorateion.  WARNING: If you invoke docker-tag-% for multiple stages in the docker file, the undecorated tags WILL CLOBBER each other.  You should pay particular attention to how this interacts with the docker publishing targets.
docker-tag-%:  docker-build-%
	$(DOCKER_EXE) tag  "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_SHA)"
	$(DOCKER_EXE) tag  "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_NAME):$(DOCKER_TAG_VERSION)"
	$(DOCKER_EXE) tag  "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)"
	$(DOCKER_EXE) tag  "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD_AND_SHA)"


docker-fqtag-%: ## Tag the local docker image for the stage '%' with fully qualified name and tags suitable for publication to the the container registry. Some of the tags will omit the stage decoration.  WARNING: If you invoke docker-fqtag-% for multiple stages in the docker file, the undecorated tags WILL CLOBBER each other.  You should pay particular attention to how this interacts with the docker publishing targets.
docker-fqtag-%:  docker-build-%
docker-fqtag-%:  docker-tag-%
	$(DOCKER_EXE) tag  "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION_AND_SHA)-$*"
	$(DOCKER_EXE) tag  "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION)-$*"
	$(DOCKER_EXE) tag  "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*"
	$(DOCKER_EXE) tag  "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION_AND_BUILD_AND_SHA)-$*"
#
	$(DOCKER_EXE) tag  "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION_AND_SHA)"
	$(DOCKER_EXE) tag  "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION)"
	$(DOCKER_EXE) tag  "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION_AND_BUILD)"
	$(DOCKER_EXE) tag  "$(DOCKER_NAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*" "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION_AND_BUILD_AND_SHA)"



docker-publish-%: ## Publish the latest docker image for the stage '%' to the docker registry.  WARNING: If multiple stages are publised to the registry, docker tags that omit the stage decorator WILL clobber eachother.
docker-publish-%: docker-fqtag-%
	$(DOCKER_EXE) push "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION_AND_SHA)-$*"
	$(DOCKER_EXE) push "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION)-$*"
	$(DOCKER_EXE) push "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION_AND_BUILD)-$*"
	$(DOCKER_EXE) push "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION_AND_BUILD_AND_SHA)-$*"
#
	$(DOCKER_EXE) push "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION_AND_SHA)"
	$(DOCKER_EXE) push "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION)"
	$(DOCKER_EXE) push "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION_AND_BUILD)"
	$(DOCKER_EXE) push "$(DOCKER_FQNAME):$(DOCKER_TAG_VERSION_AND_BUILD_AND_SHA)"



# TODO: Does this belong here? or is this too Dockerfile specific?
# TODO: a defshell should probably have the source dirs bind mounted, which is very Dockerfile specific.
# docker-run-builder-shell: ## Start an interactive /bin/sh development shell in the builder docker
# docker-run-builder-shell: docker-build-builder
#	$(DOCKER_EXE) run -ti --rm --entrypoint /bin/sh  "$(DOCKER_NAME):$(DOCKER_TAG_VERSION)-builder"


docker-info: ## Print information about the docker build
	@echo "Docker name                        (DOCKER_NAME)                          : $(DOCKER_NAME)"
	@echo "Docker registry                    (DOCKER_REGISTRY)                      : $(DOCKER_REGISTRY)"
	@echo "Docker FQ name                     (DOCKER_FQNAME)                        : $(DOCKER_FQNAME)"
	@echo "Docker tag (version)               (DOCKER_TAG_VERSION)                   : $(DOCKER_TAG_VERSION)"
	@echo "Docker tag (sha)                   (DOCKER_TAG_VERSION_AND_SHA)           : $(DOCKER_TAG_VERSION_AND_SHA)"
	@echo "Docker tag (build)                 (DOCKER_TAG_VERSION_AND_BUILD)         : $(DOCKER_TAG_VERSION_AND_BUILD)"
	@echo "Docker tag (build and sha)         (DOCKER_TAG_VERSION_AND_BUILD_AND_SHA) : $(DOCKER_TAG_VERSION_AND_BUILD_AND_SHA)"
	@echo "Docker tag local build decorator   (DOCKER_DEVELOPMENT_DECORATOR)         : $(DOCKER_DEVELOPMENT_DECORATOR)"


info:: docker-info

.PHONY:: docker-info


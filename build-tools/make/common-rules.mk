help:  ## Show this help.
#   The awk command shows fancy colors, but it omits my pattern targets.
#	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | grep -v '^#' | sort | sed -e 's/:://' -e 's/://'|  awk -F' *## *' '{printf "%-25s : %s\n", $$1, $$2}'

#$(BUILD_DIR):
#	mkdir -p $(@)

#builddir-clean: ## Clean the build dir
#	rm -rf $(BUILD_DIR)


info:: ## Print build information
	@echo "Project Name           (PROJ_NAME)       : $(PROJ_NAME)"
	@echo "Current user           (USER_NAME)       : $(USER_NAME)"
	@echo "Git branch slug        (GIT_BRANCH_SLUG) : $(GIT_BRANCH_SLUG)"
	@echo "Git commit sha         (GIT_SHA)         : $(GIT_SHA)"
	@echo "Git commit sha (short) (GIT_SHA_SHORT)   : $(GIT_SHA_SHORT)"
	@echo "Git commit sha (long)  (GIT_SHA_LONG)    : $(GIT_SHA_LONG)"
	@echo "Timestamp              (TIMESTAMP)       : $(TIMESTAMP)"
#	@echo "BUILD_DIR              (BUILD_DIR)       : $(BUILD_DIR)"

clean:: ## Run all clean targets
#clean:: builddir-clean

.PHONY:: help
.PHONY:: info
.PHONY:: clean

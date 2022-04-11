go-build: ## Build the go program locally
	@echo "Local Go pattern rules not complete.  Mostly using docker so far."
	false
	$(GO_EXE) build -o $(GO_TARGET_DIR)/bin/$(GO_TARGET_EXE)

go-run: ## Run the go program locally
	@echo "Local Go pattern rules not complete.  Mostly using docker so far."
	false
	$(GO_EXE) run $(GO_PROJECT_SRC)/

go-test: ## Test the go program locally
	@echo "Local Go pattern rules not complete.  Mostly using docker so far."
	false
	$(GO_EXE) test 

go-coverage: ## Test the go program locally
	@echo "Local Go pattern rules not complete.  Mostly using docker so far."
	false
	$(GO_EXE) test -coverprofile "$(GO_PROJECT_SRC)/SOME_BUILD_DIR/$(GO_TARGET_EXE).cp.out"
	$(GO_EXE) tool cover -html="$(GO_PROJECT_SRC)/SOME_BUILD_DIR/$(GO_TARGET_EXE).cp.out"

go-lint: ## Lint the go program locally
	@echo "Local Go pattern rules not complete.  Mostly using docker so far."
	false
	$(GOLINT_EXE) run --enable-all

go-clean: ## Clean up the local go program build
	@echo "Local Go pattern rules not complete.  Mostly using docker so far."
	false

go-info: ## Print information about the GO build
	@echo "GO executable      (GO_EXE)           : $(GO_EXE)"
	@echo "GO project main    (GO_PROJECT_MAIN)  : $(GO_PROJECT_MAIN)"

info:: go-info

.PHONY:: go-info
.PHONY:: go-run

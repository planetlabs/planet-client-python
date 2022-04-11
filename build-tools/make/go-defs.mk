GO_EXE:=$(if $(strip $(GO_EXE)),$(strip $(GO_EXE)),go)
GOLINT_EXE:=$(if $(strip $(LINT_EXE)),$(strip $(GOLINT_EXE)),golangci-lint)
GO_PROJECT_SRC:=$(if $(strip $(GO_PROJECT_SRC)),$(strip $(GO_PROJECT_SRC)),src)

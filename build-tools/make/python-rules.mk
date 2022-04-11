python-info: ## Print information about the python build
	@echo "Python Project Name         (PYTHON_PROJ_NAME)  : $(PYTHON_PROJ_NAME)"
	@echo "Python Virtual Environment  (PYTHON_VENV)       : $(PYTHON_VENV)"
	@echo "Python executable           (PYTHON_EXE)        : $(PYTHON_EXE)"

python-venv: ## Bootstrap a local python virtual environment with only the minimal runtime requirements.
	$(PYTHON_EXE) -m venv "$(PYTHON_VENV)"
	( . $(PYTHON_VENV)/bin/activate && python -m pip install -e . )
#	( . $(PYTHON_VENV)/bin/activate && python -m pip install  . )

python-venv-%: ## Bootstrap a local python virtual with the extra requires identified by '%'
python-venv-%: python-venv
	( . $(PYTHON_VENV)/bin/activate && python -m pip install -e .[$*] )

python-venv-clean: ## Destroy the local python virtual environment
#	. $(PYTHON_VENV)/bin/activate && python setup.py clean
	rm -rf $(PYTHON_VENV)
#	rm -rf *.egg-info
#	rm -rf $(PYTHON_PROJ_NAME).egg-info
#	find . -name __pycache__ -exec rm -rf {} \;

python-pytest: ## Run python pytest in the virtual environment. The virtual environment must already be boostrapped with the necessary extra test requirements.
#	( . $(PYTHON_VENV)/bin/activate && pytest --log-cli-level=DEBUG tests )
	( . $(PYTHON_VENV)/bin/activate && pytest tests )

python-nox: ## Run python nox tests in the virtual environment. The virtual environment must already be boostrapped with the necessary extra test requirements.
	( . $(PYTHON_VENV)/bin/activate && nox )


info:: python-info

clean:: python-venv-clean

.PHONY:: python-info
.PHONY:: python-venv
.PHONY:: python-venv-clean
.PHONY:: python-pytest

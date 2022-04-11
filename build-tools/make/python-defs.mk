PYTHON_PROJ_NAME:=$(if $(strip $(PYTHON_PROJ_NAME)),$(strip $(PYTHON_PROJ_NAME)),$(PROJ_NAME))
PYTHON_EXE:=$(if $(strip $(PYTHON_EXE)),$(strip $(PYTHON_EXE)),python3.9)
PYTHON_VENV=venv.$(PYTHON_PROJ_NAME)

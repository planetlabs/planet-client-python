VERSION:=$(if $(VERSION),$(VERSION),$(shell cat $(PROJ_ROOT)/version.txt))
BUILD_NUM:=$(if $(CI_PIPELINE_IID),$(CI_PIPELINE_IID),dev$(TIMESTAMP))

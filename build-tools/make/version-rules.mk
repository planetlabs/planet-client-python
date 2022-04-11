# TODO: should we have any synchronization between release brach names and version.txt or VERSION?
# TODO: we are not currently doing anything to drop git tags at released versions.
# TODO: I really should create tmp files in a .build directory

.PHONY:: version-with-buildnum.txt

version-with-buildnum.txt: ## Create a version file that includes the build number.
	echo $(VERSION).$(BUILD_NUM) > $@

version-bump-major: ## Bump the major version number, reset the minor ant patch number to zero
	awk -F. '{print $$1+1 ".0.0"}' $(PROJ_ROOT)/version.txt > version.txt.build
	mv -f version.txt.build $(PROJ_ROOT)/version.txt

version-bump-minor: ## Bump the major minor number, reset patch level to zero
	awk -F. '{print $$1 "." $$2+1 ".0"}' $(PROJ_ROOT)/version.txt > version.txt.build
	mv -f version.txt.build $(PROJ_ROOT)/version.txt

version-bump-patch: ## Bump the patch version number
	awk -F. '{print $$1 "." $$2 "." $$3+1}' $(PROJ_ROOT)/version.txt > version.txt.build
	mv -f version.txt.build $(PROJ_ROOT)/version.txt

version-info: ## Print version information
	@echo "Version             (VERSION)            : $(VERSION)"
	@echo "Build number        (BUILD_NUM)          : $(BUILD_NUM)"

version-clean: ## Clean version files
	rm -f version.txt.build
	rm -f version-with-buildnum.txt

info:: version-info

clean:: version-clean

.PHONY:: version-bump-major
.PHONY:: version-bump-minor
.PHONY:: version-bump-patch
.PHONY:: version-info
.PHONY:: version-clean

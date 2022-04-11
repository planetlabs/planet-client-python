# Common build tools

Common build tool. The contents of this directory should be project agnostic.

## Makefiles
Makefile modules are provided for common build targets. Their use is encouraged
to promote commonality of development practices.  Many of the makefile
modules assume that they will be consumed by a "micro makefile" that is
only responsible for single taget.  It is only necessary to include the modules
that will be required for a given build.

Generally, each module takes the form of two `.mk` files that should be included:
a "defs" file, which should be included near the top of the consuming makefile, and
a "rules" file, which should be included later.  Modules should define an `info`
target, and pattern rules will be wired to work with the common module's `help`
target.  See each module for specific details. (TODO: we should have proper
documentation for each module.)

An example `Makefile` that will pull in all rules required to build, run, tag, and publish
a docker image from a single `Dockerfile` in the current directory.
:
```
# PROJ_NAME is used by many modules to default the resulting artifact name.
#           Most modules provide a way to overide this default as well.
# PROJ_ROOT is used by some modules that assume they operate at a project scope,
            and require knowledge of the project root directory.  Many modules
            do not require this, and operate on the local directory.
PROJ_NAME:=my_project
PROJ_ROOT:=$(dir $(firstword $(MAKEFILE_LIST)))
MK_DIR:=$(PROJ_ROOT)/../build-tools/make

include $(MK_DIR)/common-defs.mk
include $(MK_DIR)/version-defs.mk
include $(MK_DIR)/docker-defs.mk

default: help

include $(MK_DIR)/common-rules.mk
include $(MK_DIR)/version-rules.mk
include $(MK_DIR)/docker-rules.mk
include $(MK_DIR)/printenv-rules.mk
```

Example Usage:
```
bash$ make help
clean                     : Run all clean targets
docker-build-%            : Build and tag the docker stage '%'. The value of '%' is a wildcard, and will be expanded at runtime.
docker-fqtag-%            : Tag the local docker image for the stage '%' with fully qualified name and tags suitable for publication to the the container registry. Some of the tags will omit the stage decoration.  WARNING: If you invoke docker-fqtag-% for multiple stages in the docker file, the undecorated tags WILL CLOBBER each other.  You should pay particular attention to how this interacts with the docker publishing targets.
docker-info               : Print information about the docker build
docker-publish-%          : Publish the latest docker image for the stage '%' to the docker registry.  WARNING: If multiple stages are publised to the registry, docker tags that omit the stage decorator WILL clobber eachother.
docker-run-%              : Execute the entrypoint for docker stage '%'. The value of '%' is a wildcard, and will be expanded at runtime.
docker-tag-%              : Tag the local docker image for the stage '%' with tags that omit the stage decorateion.  WARNING: If you invoke docker-tag-% for multiple stages in the docker file, the undecorated tags WILL CLOBBER each other.  You should pay particular attention to how this interacts with the docker publishing targets.
help                      : Show this help.
info                      : Print build information
```

```
bash$ make info
Project Name                  : my_project
Current user                  : user-name
Git branch slug               : develop
Git commit sha                : 14758f1afd44c09b7992073ccf00b43dc65f4ad0
Git commit sha (short)        : 14758f1
Timestamp                     : 20210317180716
Environment:
.
.
.
```

```
bash$ make docker-build-runtime
docker building : runtime
docker build --target "runtime" -t "my_project:1.0.0.dev20210317181103--development--user-name-runtime" .
.
.
.
```

```
bash$ make docker-run-utest
docker building : utest
docker build --target "utest" -t "my_project:1.0.0.dev20210317181156--development--user-name-utest" .
.
.
.
docker run --rm  "my_project:1.0.0.dev20210317181156--development--user-name-utest"
.
.
.
```

### TODO
- There is an implied order makefiles modules should be included in to properly resolve macros, but this is not documented or obvious.
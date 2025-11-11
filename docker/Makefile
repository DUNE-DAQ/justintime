
DCKR_MAKE_HERE:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
DCKR_BASE_IMG=ghcr.io/dune-daq/alma9-minimal:latest
# DUNEDAQ_RELEASE=rc-v4.0.0-1
JINT_ROOT=$(shell git rev-parse --show-toplevel)
JINT_BRANCH=$(shell git describe --tags --exact-match 2> /dev/null \
  || git symbolic-ref -q --short HEAD \
  || git rev-parse --short HEAD)
DCKR_TAG=justintime
DCKR_VERSION=$(shell echo ${JINT_BRANCH} | sed 's|/|_|g')
BUILD_AREA=${DCKR_MAKE_HERE}/workarea
BUILD_AREA=/tmp/${USER}/justintime/${DCKR_VERSION}
RUN_AREA=/tmp/${USER}/justintime/${DCKR_VERSION}/workarea

DCKR_OPTS=--user $(shell id -u):$(shell id -g) \
    -it \
    --rm \
    -v /etc/passwd:/etc/passwd:ro -v /etc/group:/etc/group:ro \
    -v /cvmfs/dunedaq.opensciencegrid.org:/cvmfs/dunedaq.opensciencegrid.org:ro \
    -v /cvmfs/dunedaq-development.opensciencegrid.org:/cvmfs/dunedaq-development.opensciencegrid.org:ro

.PHONY: info
info: 
	@echo just-in-time root: ${JINT_ROOT}
	@echo just-in-time tag/branch/hash: ${JINT_BRANCH}
	@echo build area: ${BUILD_AREA}
	@echo run area: ${RUN_AREA}
	@echo docker tag: ${DCKR_TAG}
	@echo docker version: ${DCKR_VERSION}

connection-check: ## Check that GPN connection is available
	@curl  --connect-timeout 1 github.com &> /dev/null


.PHONY: all
all: connection-check  workarea gits dunedaq justintime image ## Build all targets

.PHONY: workarea 
workarea: ## Create dunedaq work area
	@[ "${DUNEDAQ_RELEASE}" ] || ( echo ">> DUNEDAQ_RELEASE is not set. Usage: make $@ DUNEDAQ_RELEASE=<version>"; exit 1 )
	@echo "------------------------------------------"
	@echo "🚧 Creating new workarea 🚧"
	@echo "------------------------------------------"
	mkdir -p ${RUN_AREA}
	docker run ${DCKR_OPTS} \
        -v /nfs:/nfs:ro \
        -v ${RUN_AREA}:/dunedaq/run:z \
        -v ${DCKR_MAKE_HERE}/create_workarea.sh:/dunedaq/bin/create_workarea.sh \
        ${DCKR_BASE_IMG} \
        -c "export PATH=\"/dunedaq/bin/:$$PATH\"; cd /dunedaq/run; create_workarea.sh ${DUNEDAQ_RELEASE}"

${RUN_AREA}/dunedaq-area/sourcecode/detchannelmaps: connection-check
    git -C ${RUN_AREA}/dunedaq-area/sourcecode/ clone https://github.com/DUNE-DAQ/detchannelmaps.git -b thea/inverse_map


.PHONY: dunedaq 
dunedaq: ## Build extra dunedaq packages
	@echo "------------------------------------------"
	@echo "🛠 Building work area 🛠"
	@echo "------------------------------------------"
	docker run ${DCKR_OPTS} \
        -v ${RUN_AREA}:/dunedaq/run:z \
        -w /dunedaq/run/dunedaq-area \
        ${DCKR_BASE_IMG} \
        -c "source ./quick_env.sh; dbt-build"

.PHONY: justintime
justintime: ## Install justintime and its dependencies
	@echo "------------------------------------------"
	@echo "🐍 Installing justintime and its dependencies🐍"
	@echo "------------------------------------------"
	cp -r ${JINT_ROOT}/ ${RUN_AREA}/justintime
	@docker run ${DCKR_OPTS} \
        -v /nfs:/nfs:ro \
        -v ${RUN_AREA}:/dunedaq/run:z \
        --env HTTP_PROXY=${HTTP_PROXY} \
        --env HTTPS_PROXY=${HTTPS_PROXY} \
        --env NO_PROXY=${NO_PROXY} \
        -w /dunedaq/ \
        ${DCKR_BASE_IMG} \
        -c "cd run/dunedaq-area; source quick_env.sh; cd ../justintime; pip install -e ."

image: ## Build docker image
	@echo "------------------------------------------"
	@echo "📦 Building image 📦"
	@echo "------------------------------------------"
	cp ${DCKR_MAKE_HERE}/{Dockerfile,entrypoint.sh} ${BUILD_AREA}
	docker buildx build --tag ${DCKR_TAG}:${DCKR_VERSION} --tag ${DCKR_TAG}:latest ${BUILD_AREA}

.PHONY: clean
clean: ## Clean the build area
	@echo "------------------------------------------"
	@echo "🧹 Clearing old workarea 🧹"
	@echo "------------------------------------------"
	rm -rf ${BUILD_AREA}

.PHONY: gits
gits: ${RUN_AREA}/dunedaq-area/sourcecode/detchannelmaps 


.PHONY: help
help: ## Display this help
	@IFS=$$'\n'; for line in `grep -h -E '^[a-zA-Z_#-]+:?.*?## .*$$' $(MAKEFILE_LIST)`; do if [ "$${line:0:2}" = "##" ]; then \
	echo $$line | awk 'BEGIN {FS = "## "}; {printf "\n\033[33m%s\033[0m\n", $$2}'; else \
	echo $$line | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'; fi; \
	done; unset IFS;



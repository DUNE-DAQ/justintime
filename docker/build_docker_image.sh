#!/usr/bin/bash
# Bash/Zsh independent way of determining the source path
SH_SOURCE=${BASH_SOURCE[0]:-${(%):-%x}}
DCKR_BUILD_HERE=$(cd $(dirname ${SH_SOURCE}) && pwd)

DST_AREA="${DCKR_BUILD_HERE}/workarea"

DCKR_BASE_IMG=ghcr.io/dune-daq/c8-minimal:latest
DUNEDAQ_RELEASE=$1
DUNEDAQ_RELEASE="v3.2.2"
DCKR_TAG=justintime
JINT_BRANCH=v0.3.0
DCKR_VERSION=${JINT_BRANCH}

set -e
usage () {
    echo "This utility builds docker images containing the necessary code for DAQ applications from a release."
    echo "./build_docker_image RELEASE"
    echo "(for example ./build_docker_image v3.2.2)"
}



DCKR_OPTS="--user $(id -u):$(id -g) \
    -it \
    --rm \
    -v /etc/passwd:/etc/passwd:ro -v /etc/group:/etc/group:ro \
    -v /cvmfs/dunedaq.opensciencegrid.org:/cvmfs/dunedaq.opensciencegrid.org:ro \
    -v /cvmfs/dunedaq-development.opensciencegrid.org:/cvmfs/dunedaq-development.opensciencegrid.org:ro"

# echo "------------------------------------------"
# echo "Clearing old workarea"
# echo "------------------------------------------"
# rm -rf ${DST_AREA}
# mkdir -p ${DST_AREA}
# docker run ${DCKR_OPTS} \
#     -v /nfs:/nfs:ro \
#     -v ${DST_AREA}:/dunedaq/run:z \
#     -v ${DCKR_BUILD_HERE}/create_workarea.sh:/dunedaq/bin/create_workarea.sh \
#     ${DCKR_BASE_IMG} -- \
#     "export PATH=\"/dunedaq/bin/:\$PATH\"; cd /dunedaq/run; create_workarea.sh ${DUNEDAQ_RELEASE}"

# cd ${DST_AREA}/dunedaq-area/sourcecode
# git clone https://github.com/DUNE-DAQ/detchannelmaps.git -b thea/inverse_map
# cd ${DST_AREA}/
# git clone https://github.com/DUNE-DAQ/justintime.git -b ${JINT_BRANCH}


# echo "------------------------------------------"
# echo "Building work area"
# echo "------------------------------------------"
# docker run ${DCKR_OPTS} \
#     -v /nfs:/nfs:ro \
#     -v ${DST_AREA}:/dunedaq/run:z \
#     -w /dunedaq/run/dunedaq-area \
#     ${DCKR_BASE_IMG} -- \
#     "source env.sh; dbt-build"


# echo "------------------------------------------"
# echo "Installing extra python package"
# echo "------------------------------------------"
# docker run ${DCKR_OPTS} \
#     -v /nfs:/nfs:ro \
#     -v ${DST_AREA}:/dunedaq/run:z \
#     --env HTTP_PROXY=${HTTP_PROXY} \
#     --env HTTPS_PROXY=${HTTPS_PROXY} \
#     --env NO_PROXY=${NO_PROXY} \
#     -w /dunedaq/ \
#     ${DCKR_BASE_IMG} -- \
#     "cd run/dunedaq-area; source env.sh; cd ../justintime; pip install -e ."



echo "------------------------------------------"
echo "Building image"
echo "------------------------------------------"
set -x
docker buildx build --tag ${DCKR_TAG}:${DCKR_VERSION} ${DCKR_BUILD_HERE} 

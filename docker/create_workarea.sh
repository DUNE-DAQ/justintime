#!/bin/bash
usage() {
    echo "Usage: $0 <dune|fd|nd>daq-<version>-<a9|c8>"
    echo "where the <version> format is vX.Y.Z"
    echo "For a candidate release, the format is <dune|fd|nd>daq-<version>-rc<iteration>-<a9|c8>"
    exit 1
}

if [ "$#" -ne 1 ]; then
    echo "You must provide a release name as a single argument"
    usage
fi

DUNEDAQ_RELEASE=$1
# "rc" denotes a candidate release, as opposed to frozen
if [[ "$DUNEDAQ_RELEASE" = *"rc-"* ]]; then
    DBT_CREATE_OPTS="-b candidate"
fi

# Parse necessary dbt version from the release symbolic link
DBT_DIR=/cvmfs/dunedaq.opensciencegrid.org/tools/dbt/
DBT_RELEASE=$(echo $DUNEDAQ_RELEASE | cut -d'-' -f1-2)
if [ -e ${DBT_DIR}/$DBT_RELEASE ]; then
    DBT_VERSION=$(readlink -f ${DBT_DIR}/$DBT_RELEASE | rev | cut -d'/' -f1 | rev)
    echo "DBT version for $RELEASE: $DBT_VERSION"
else
    echo "Error: Symbolic link not found for $DBT_RELEASE in $DBT_DIR."
    usage
    exit 1
fi

source /cvmfs/dunedaq.opensciencegrid.org/setup_dunedaq.sh
echo "------------------------------------------"
echo "Loading daq-buildtool environment"
echo "------------------------------------------"
echo "DBT version: $DBT_VERSION"
setup_dbt ${DBT_VERSION}

echo "------------------------------------------"
echo "Loading daq-release workarea"
echo "------------------------------------------"
set -e # If this next step errors, stop the script
dbt-create ${DBT_CREATE_OPTS} ${DUNEDAQ_RELEASE} dunedaq-area

cd dunedaq-area
source ./env.sh

# Save environment filtering out read-only vars
declare -p | grep -v 'declare -[^ ]*r[^ ]* ' > quick_env.sh

#!/bin/bash

# Script for automating installation and execution of photofs during debugging
#
# Installs using '--user' option so not to overwrite any system-wide install

# Install path
PYTHON_USER_BASE=$(python -m site --user-base)

# Filesystem root
FS_ROOT=${1:-~/Pictures/_photofs_}


# Print error message and exit cleanly
error() {
    if [ $# -lt 1 ]; then
        echo "ERROR: An unknown error occurred." >&2
        exit 1
    fi

    echo "ERROR: $1" >&2

    # Print any remaining args as separate lines with indent aligned
    # with start of message text above.
    shift
    while [ -n "$1" ]; do
        echo "       $1" >&2
        shift
    done

    exit 1
}


python setup.py install --user || \
    error "Could not install photofs" \
          "If there are permissions errors try running:" \
          "    sudo python setup.py clean --all"


if [ ! -d "$FS_ROOT" ]; then
    mkdir -p "$FS_ROOT" || \
        error "Could not create filesystem root dir '$FS_ROOT'."
fi

# Start the FUSE filesystem in foreground to allow debugging
# Will exit on CTRL-C.
${PYTHON_USER_BASE}/bin/photofs --foreground $FS_ROOT

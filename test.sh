#!/bin/bash

# Copyright (C) 2015-2016 James Bowen
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.


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

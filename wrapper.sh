#!/bin/bash

# Wrapper script around Lyve-SET commands

# Get the parent directory of the script directory.
# Script should be in $ENV_DIR/bin, so this should be the root directory of the
# Conda environment.
ENV_DIR=$(dirname $(dirname $(readlink -f $0)))

export LYVESET_DIR="$ENV_DIR/opt/lyve-set"
export PATH="$LYVESET_DIR/scripts:$PATH"

if [# -eq 0 ]; then
	# No arguments, print usage and available commands

	cat <<- EOF
	Wrapper around Lyve-SET scripts

	usage: $(basename $0) COMMAND [COMMAND_ARGS...]


	Available Lyve-SET commands:

	EOF
	ls "$LYVESET_DIR/scripts" | sort

else
	# Run command

	CMD=$1
	shift
	"$LYVESET_DIR/scripts/$CMD" "$@"

fi

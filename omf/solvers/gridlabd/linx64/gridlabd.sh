#!/bin/bash

if [ -h "$0" ]; then
	BINPATH=`readlink "$0"`
	if [ "${BINPATH:0:1}" != "/" ]; then
		BINPATH="$(dirname "$0")/$BINPATH"
	fi
else
	BINPATH="$0"
fi
CURDIR=`dirname "$BINPATH"`

pushd "$CURDIR" > /dev/null
export GRIDLABD="$PWD"
if [ -n "$GLPATH" ]; then
	export GLPATH="$PWD:$GLPATH"
else
	export GLPATH="$PWD"
fi
popd > /dev/null

echo "binpath $BINPATH"
echo "curdir $CURDIR"
echo "glpath $GLPATH"
echo "gridlabd=$GRIDLABD"

"$GRIDLABD/gridlabd.bin" "$@"

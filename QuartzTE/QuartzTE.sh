#!/bin/bash
thisdir=$(dirname "$0")
cd $thisdir

python3 QuartzTE.py "$@"

cd $HOME

#!/bin/sh
script_dir=$(dirname $0)
cd $script_dir
python $script_dir/web.py
read -n1 -r -p "Server stopped. Press space to continue..." key

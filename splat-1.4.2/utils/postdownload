#!/bin/bash

# Simple script for processing of downloaded undelimited gzipped
# USGS DEM files, and converting them to SPLAT Data Files.
# Written by John A. Magliacane, KD2BD May 2002.
# Last modified on Sunday 01-Mar-09.

if [ "$#" = "0" ]; then
	echo
	echo "This utility reads downloaded gzipped USGS DEM"
	echo "files and generates equivalent SPLAT Data Files (SDFs)."
	echo
	echo "Files compatible with this SPLAT! utility may be"
	echo "obtained at:"
	echo
	echo "http://edcftp.cr.usgs.gov/pub/data/DEM/250/"
	echo
	echo "Usage: postdownload wilmington-w.gz"
	echo
else
	# gunzip the downloaded file...
	echo -n "Uncompressing $1..."
	gunzip -c $1 > unzipped_file
	echo
	echo "Adding record delimiters..."
	dd if=unzipped_file of=delimited_file ibs=4096 cbs=1024 conv=unblock
	# Invoke usgs2sdf to generate a SPLAT Data File...
	usgs2sdf delimited_file
	echo -n "Removing temp files..."
	rm delimited_file unzipped_file
	echo
	echo "Done!"
fi


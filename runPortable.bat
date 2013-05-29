:: This batch file starts the USB key portable version of the OMF.
cd .\omf\
echo on
start .\..\ppython27\App\python.exe omf.py
sleep 5
start .\..\GoogleChromePortable\GoogleChromePortable.exe http://localhost:5001
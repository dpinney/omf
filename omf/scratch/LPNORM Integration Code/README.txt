LPNORM.zip
By Mannan.Javid@NRECA.coop in September 2016

DESCRIPTION
This zip file integrates OMF data with RDT. It runs the script lpnorm.py which takes in an omf-formatted feeder (.omd) and vars.json file to run an RDT simulation. It formats the feeder as an RDT input json and generates a made-up fragility scenario to test against. Simple_Market_System.json and vars.json are JSON formatted files of the feeder and RDT specific inputs saved in the inData folder.

REQUIREMENTS
- Python 2.7x (https://www.python.org)
- OMF (https://github.com/dpinney/omf)
- RDT (https://github.com/lanl-ansi/micot-rdt)
- SCIP (http://scip.zib.de)
- Java 7 (https://www.java.com/en/)

RUN PROCEDURE
- Extract zip contents.
- Copy the contents of micot-application-rdt.zip, micot-libraries.zip, and the file SimpleFragilityEngine_0.3.jar to /bin folder.
- Run the command 'python lpnorm.py Simple_Market_System.json vars.json' on a unix command line.

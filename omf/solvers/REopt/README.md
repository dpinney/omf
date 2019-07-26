Running REopt API Analysis using Python
==========================================

[REopt](https://reopt.nrel.gov/) is a techno-economic decision support model from NREL which is used for optimizing energy systems for buildings, campuses, communities, and microgrids. [REopt Lite](https://reopt.nrel.gov/tool) offers a no-cost subset of features from NREL's more comprehensive REopt model. REopt Lite also offers an application programming interface (API). This is a guide to use REopt's Application Programming Interface for running REopt analysis programmatically. 

**Detailed documentation of REopt Lite API is available [here](https://developer.nrel.gov/docs/energy-optimization/reopt-v1/).**

## How to run?
  ### Prerequisites 
  You will need a python 2.7/3 interpreter:   
  - Ubuntu: `sudo apt-get install python3-dev`
  - Mac OSX: [Refer this page if you need help](https://docs.python-guide.org/starting/install3/osx/)
  - Windows: [Download and install version 3.5.5 from here](https://www.python.org/downloads/windows/)
      _**Note** that Python 3.5.5 cannot be used on Windows XP or earlier._
  - Install [pip](https://pip.pypa.io/en/stable/installing/)
  
  And add the following packages:
  - `pip install requests json time logging`  
  
  Install git:
  - https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
  
  ### Running the code
  1. Clone (or download) the repository: 
  
  `git clone https://github.com/nrel/REopt-API-Analysis.git`
  
  2. Open/Run the python script [post\_and\_poll.py](post\_and\_poll.py)
  

## File Descriptions

**Note**: in the script  named post\_and\_poll.py replace "my_API_KEY" with your API key. You can obtain your API key from developer.nrel.gov/signup/ (no cost). 

### Scenario_POST.json
The inputs to the model are sent in json format. POST.json contains an example post where the assessment of economic feasibiity of photovoltaic generation and battery storage is being done for a given location with a custom electric tariff.

### post\_and\_poll.py
A scenario is posted at [https://developer.nrel.gov/api/reopt/v1/job/](https://developer.nrel.gov/api/reopt/v1/job/) to get a **Universal Unique ID** (run_uuid) back. This script is for posting inputs to the API, receive the run_uuid and then polling for results using the run_uuid.

### results\_poller.py
A polling function for retrieving results. This function is utilized in the post\_and\_poll.py. 

### logger.py
Configurable logging for console and log file


**The results will get saved in results.json.**

## Running different Scenarios
- In the script named _post\_and\_poll.py_ replace the file name 'Scenario_POST.json' to {Scenario_POST1, Scenario_POST2 etc.} in the following line of the code:
  `post = json.load(open('Scenario_POST.json'))`

- In the same script, for saving the results in different files, replace the file name 'results.json' to a different name in the following line of the code:
 ` results_file = 'results.json'`



mmm.solvers.der-cam

Solver for Lawrence Berkeley National Laboratory (LBNL) DER-CAM API

Before running:
- acquire an API key : request a DER-CAM account here: https://dercam-app.lbl.gov/

# Functions (WIP)
`__init__.py`
```
>> run ( path, modelFile="", reoptFile="", timeout=0 )

>> print_existing_models ( userKey )
```

# Input options:

- modelFile : single-node or multi-node input (Excel file)
- reoptFile : REopt.jl input (json file) -> Scenario_test_POST.json

# Outputs:

- results.csv
- results-nodes.csv 

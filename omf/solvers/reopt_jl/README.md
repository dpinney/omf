omf.solvers.reopt_jl

Solver for Julia verison of REopt. 

# Dependencies:
- python@3.11 (other versions of python3 may work)
- packages in install_reopt_jl(system) <- runs automatically within run_reopt_jl 

# Usage:

__init__.py:
- run_reopt_jl(path, inputFile="", default=False, convert=True, outages=False, microgrid_only=False,
                 solver="HiGHS", solver_in_filename=True, max_runtime_s=None)

General paramters:
- path: directory containing inputFile ; output files written here as well
- inputFile: json file containing REopt API input information
    - if this file is already converted for REopt.jl -> set convert=False
- default: if True, sets inputFile to default values, uses given inputFile otherwise
- convert: if True, converts variables names to those used in REopt.jl, no conversion otherwise
- outages: if True, runs outage simulation, otherwise doesn't
- microgrid_only: if True runs without grid, otherwise runs as normal
    *only used within REopt.jl currently (not API)
- max_runtime_s: default is None, otherwise times at after given number of seconds and returns local optimal value (may not be the global optimum)

Testing parameters:
- solver: set to HiGHS (best runtime performance) ; other available options: SCIP
- solver_in_filename: puts solver in filename if True

Examples:

>>> run_reopt_jl(currentDir, inputFile="path/to/inputFile.json")
writes ouput file from REopt.jl to "currentDir/out_HiGHS_inputFile.json"

>>> run_reopt_jl(currentDir, default=True)
uses julia_default.json as input and writes ouput file from REopt.jl to "currentDir/out_julia_default.json" 

>>> run_reopt_jl(currentDir, inputFile="path/to/inputFile.json", solver_in_filename=False)
writes output file from REopt.jl to "currentDir/out_inputFile.json"

>>> run_reopt_jl(currentDir, inputFile="path/to/inputFile.json", outages=True)
writes ouput file from REopt.jl to "currentDir/out_HiGHS_inputFile.json" and
writes outage output fie to "currentDir/outages_HiGHS_inputFile.json"

Testing usage (work in progress):

- __init__.py: 
    - runAllSolvers(path, testName, fileName="", default=False, convert=True, outages=True, 
                  solvers=["SCIP","HiGHS"], solver_in_filename=True, max_runtime_s=None,
                  get_cached=True )

Usage: simlar to run_reopt_jl but takes in list of solvers and runs each one on the given test case ; outputs runtime comparisons

Inputs:
- path : run_reopt_jl path
- testName : name used to identify test case
- fileName : run_reopt_jl inputFile
- default : run_reopt_jl default
- convert : run_reopt_jl convert
- outages : run_reopt_jl outages
- solvers : list of solvers to call run_reopt_jl with
- solver_in_filename : run_reopt_jl solver_in_filename
- get_cached : loads previous output file from run_reopt_jl if found at path/out_fileName
    - used to display previous results without re-running test

- test_outputs.py:
    - html_comparison(all_tests)

Inputs: 
- all_tests = [ (outPath, outagePath, testName, runtime, solver, outages, get_cached), ... ]
    - outPath = path/out_fileName
    - outagePath = path/outages_fileName
    - testName = runAllSolvers testName
    - runtime = runtime of test
    - solver = current runAllSolvers solver (iterates through)
    - outages = runAllSolvers outages
    - get_cached = runAllSolvers get_cached

Outputs (can be altered based on testing goals - work in progress):
written to path/sample_comparison_test.html
- runtime comparison chart
- for each test case: 
    - general overview (parameters & runtime)
    - microgrid overview
    - financial performance overview
    - load overview graph
    - solar generation graph
    - fossil generation graph
    - battery charge source graph
    - battery charge percentage graph
    - resilience overview graph
    - outage survival probability graph

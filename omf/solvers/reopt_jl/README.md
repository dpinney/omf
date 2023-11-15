omf.solvers.reopt_jl

Solver for Julia verison of REopt. 

# Dependencies:
- python@3.11 (other versions of python3 may work)
- packages installed in install_reopt_jl()  ( runs automatically within run_reopt_jl ) and within REoptSolver/Project.toml

Building REoptSolver Julia module:
* Project.toml & Mainfest.toml are included in /REoptSolver directory but can be modified with the following:
```
~/omf/omf/solvers/reopt_jl % julia
julia> ]
(@v1.9) pkg> activate REoptSolver
(REoptSolver) pkg> update/rm <package_name>
(REoptSolver) pkg> instantiate
(REoptSolver) pkg> build
```

# Usage:

__init __.py:
- run_reopt_jl(path, inputFile="", default=False, convert=True, outages=False, microgrid_only=False,
                 solver="HiGHS", max_runtime_s=None)

General paramters:
- path: directory containing inputFile ; output files written here as well
- inputFile: json file containing REopt API input information
    - if this file is already converted for REopt.jl -> set convert=False
- default: if True, sets inputFile to default values, uses given inputFile otherwise
- convert: if True, converts variables names to those used in REopt.jl, no conversion otherwise
- outages: if True, runs outage simulation, otherwise doesn't
- microgrid_only: if True runs without grid, otherwise runs as normal
    *only used within REopt.jl currently (not API)
- max_runtime_s: default is None, otherwise times out after given number of seconds and returns local optimal value (may not be the global optimum)

Testing parameters:
- solver: set to HiGHS (best runtime performance) ; other available options: SCIP 
    (add SCIP package to project [instructions above] & update imports in REoptSolver.jl in order to utilize)

Examples:
``` >>> run_reopt_jl(currentDir, inputFile="Scenario_test_POST.json") ```
writes ouput file from REopt.jl to "currentDir/results.json"

``` >>> run_reopt_jl(currentDir, default=True) ```
uses julia_default.json as input and writes ouput file from REopt.jl to "currentDir/results.json" 

``` >>> run_reopt_jl(currentDir, inputFile="Scenario_test_POST.json", outages=True) ```
writes ouput file from REopt.jl to "currentDir/results.json" and
writes outage output fie to "currentDir/resultsResilience.json"

Testing usage (work in progress):

- __ init__.py: 
    - runAllSolvers(path, testName, fileName="", default=False, convert=True, outages=True, 
                  solvers=["SCIP","HiGHS"], max_runtime_s=None, get_cached=True )

Usage: simlar to run_reopt_jl but takes in list of solvers and runs each one on the given test case ; outputs runtime comparisons

Inputs:
- path : run_reopt_jl path
- testName : name used to identify test case
- fileName : run_reopt_jl inputFile
- default : run_reopt_jl default
- convert : run_reopt_jl convert
- outages : run_reopt_jl outages
- solvers : list of solvers to call run_reopt_jl with

- test_outputs.py => DEPRECATED (can be found in REopt_replacements in wiires repository)

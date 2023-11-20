omf.solvers.reopt_jl

Solver for Julia verison of REopt. 

# Dependencies:
- python@3.11 (other versions of python3 may work)
- packages installed in install_reopt_jl()  ( runs automatically within run_reopt_jl )
    - julia@1.9.3
    - PyJulia (0.6.1)
- packages within REoptSolver/Project.toml ( should be installed by Project.toml & Manifest.tomnl )
    - REopt@0.32.7
    - JuMP@1.13.0
    - HiGHS@1.7.2
    - JSON (0.21.4)
    - PyCall (1.96.1)
    - PackageCompiler (2.1.10)

# Building REoptSolver Julia module:
(avoid doing this unless the package change is necessary for REoptSolver to run)
* Project.toml & Mainfest.toml are included in /REoptSolver but can be modified with the following:
```
~/omf/omf/solvers/reopt_jl % julia
julia> ]
(@v1.9) pkg> activate REoptSolver
(REoptSolver) pkg> update/rm <package_name>
(REoptSolver) pkg> instantiate
(REoptSolver) pkg> build
```
* If you make changes to REoptSolver, you will need to remove instantiate.txt (at omf/solvers/reopt_jl/) and call install_reopt_jl() in order to rebuild reopt_jl.so (sysimage for reopt_jl) 
    - You can also call run_reopt_jl with instantiate.txt removed and the rebuild & installation check will be run automatically

# Usage:
```
__init__.py:
-> run_reopt_jl(path, inputFile="", default=False, convert=True, outages=False, microgrid_only=False, max_runtime_s=None)
```

General paramters:
- path: directory containing inputFile ; output files written here as well
- inputFile: json file containing REopt API input information
    - if this file is not converted for REopt.jl -> set convert=True
- outages: if True, runs outage simulation, otherwise doesn't
- microgrid_only: if True runs without grid, otherwise runs as normal
    *only used within REopt.jl currently (not API)
- max_runtime_s: default is None, otherwise times out after given number of seconds and returns local optimal value (may not be the global optimum)

Testing parameters:
- default: if True, sets inputFile to default values found in julia_default.json, uses given inputFile otherwise
- convert: if True, converts variables names to those used in REopt.jl, no conversion otherwise

Examples:
``` 
>>> run_reopt_jl(currentDir, inputFile="Scenario_test_POST.json") 
```
writes ouput file from REopt.jl to "currentDir/results.json"

``` 
>>> run_reopt_jl(currentDir, default=True) 
```
uses julia_default.json as input and writes ouput file from REopt.jl to "currentDir/results.json" 

``` 
>>> run_reopt_jl(currentDir, inputFile="Scenario_test_POST.json", outages=True) 
```
writes ouput file from REopt.jl to "currentDir/results.json" and
writes outage output fie to "currentDir/resultsResilience.json"

# Testing usage:
```
__init__.py: 
-> runAllSolvers(path, testName, fileName="", default=False, convert=True, outages=True, solvers=["SCIP","HiGHS"], max_runtime_s=None, get_cached=True )
```

Usage: simlar to run_reopt_jl but takes in list of solvers and runs each one on the given test case ; prints out runtime comparisons
- The list of available solvers is currently limited to HiGHS to reduce compile time

Inputs:
- path : run_reopt_jl path
- testName : name used to identify test case
- fileName : run_reopt_jl inputFile
- default : run_reopt_jl default
- convert : run_reopt_jl convert
- outages : run_reopt_jl outages
- solvers : list of solvers to call run_reopt_jl with

test_outputs.py => DEPRECATED (can be found in REopt_replacements in wiires repository but needs updates to function)

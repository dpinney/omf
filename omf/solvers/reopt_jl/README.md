omf.solvers.reopt_jl

Solver for Julia verison of REopt. 

# Dependencies:
- python@3.11.7 (other versions may require you to downgrade PyCall)
- packages installed in install_reopt_jl()  ( runs automatically within run_reopt_jl )
    - julia (1.9.4)
    - PyJulia (0.6.1)
- packages within REoptSolver/Project.toml ( installed by Project.toml & Manifest.tomnl )
    - REopt@0.39.0
    - JuMP@1.17.0
    - HiGHS@1.7.5
    - JSON (0.21.4)
    - PyCall (1.96.4)
    - PackageCompiler (2.1.15)

# Building REoptSolver Julia module:
(avoid doing this unless the package change is necessary for REoptSolver to run)
* Project.toml & Manifest.toml are included in /REoptSolver but can be modified with the following:
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
-> run_reopt_jl(path, inputFile="", default=False, outages=False, microgrid_only=False, max_runtime_s=None, run_with_sysimage=True)
```

General paramters:
- path: directory containing inputFile ; output files written here as well
- inputFile: json file containing REopt API input information
    - if this file is not converted for REopt.jl -> set convert=True
- loadFile: csv load file for the given input file
    - if empty: assumes that the csv load path within inputFile is already set
    - otherwise: the path is set to path/loadFile 
- outages: if True, runs outage simulation, otherwise doesn't
- microgrid_only: if True runs without grid, otherwise runs as normal
    *only used within REopt.jl currently (not API)
- max_runtime_s: default is None, otherwise times out after given number of seconds and returns local optimal value (may not be the global optimum)
- run_with_sysimage: if True, runs with reopt_jl.so (builds beforehand if necessary), otherwise runs by loading REoptSolver project

Testing parameters:
- default: if True, sets inputFile to default values found in julia_default.json, uses given inputFile otherwise

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

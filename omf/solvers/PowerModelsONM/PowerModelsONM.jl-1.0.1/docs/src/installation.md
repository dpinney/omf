# Installation Guide

From Julia, PowerModelsONM is installed using the built-in package manager:

```julia
pkg> add PowerModelsONM
```

or equivalently,

```julia
import Pkg
Pkg.add("PowerModelsONM")
```

## Developer Installation

To install PowerModelsONM as a developer,

```julia
import Pkg
Pkg.develop(Pkg.PackageSpec(; name="PowerModelsONM", url="https://github.com/lanl-ansi/PowerModelsONM.jl"))
```

From the command-line, outside Julia, one could download the repository, either via Github.com, or using git, _i.e._,

```sh
git clone https://github.com/lanl-ansi/PowerModelsONM.jl.git
git checkout tags/v1.0.0
```

Then to install PowerModelsONM and its required packages

```sh
julia --project="path/to/PowerModelsONM" -e 'using Pkg; Pkg.instantiate(); Pkg.precompile();'
```

## Gurobi Configuration

To use Gurobi, a Gurobi binary in required on your system, as well as ENV variables defining where the Gurobi binary is, and where your Gurobi license file is, _e.g._, for Gurobi 9.10 on MacOS,

```sh
export GRB_LICENSE_FILE="$HOME/.gurobi/gurobi.lic"
export GUROBI_HOME="/Library/gurobi910/mac64"
```

__BEFORE__ importing PowerModelsONM with `using PowerModelsONM`, you __must__ `import Gurobi`.

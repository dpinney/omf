# Quick Start Guide

Once PowerModelsONM is [installed](@ref Installation-Guide), To operate PowerModelsONM several other things are required, at a minimum, a distribution data set in .dss format that includes timeseries data (e.g., LoadShapes defined and assigned to some Loads or DER assets).

The easiest way to use PowerModelsONM's complete algorithm that includes optimal switching, optimal dispatch, fault studies and stability analysis, is to use the command line interface:

```bash
julia --project=path/to/PowerModelsONM path/to/PowerModelsONM/cli/entrypoint.jl -n "path/to/network.dss" -o "path/to/output.json"
```

For complete documentation of available command line arguments see [`parse_commandline`](@ref parse_commandline).

The binary builds available on GitHub under [Releases](https://github.com/lanl-ansi/PowerModelsONM.jl/releases) may also be used in a similar manner:

```bash
path/to/PowerModelsONM_binary -n "path/to/network.dss" -o "path/to/output.json"
```

Alternatively, you may wish to use PowerModelsONM from the Julia REPL, which if you want to use custom [Optimizers](@ref) is advisable. You should have your custom solvers installed in your primary Julia environment (_e.g._, v1.6), and launch the REPL with the command:

```bash
julia --project=path/to/PowerModelsONM
```

Once in the REPL, import PowerModelsONM with:

```julia
using PowerModelsONM
```

For more detailed use of PowerModelsONM from the REPL, read the [Beginner's Tutorial](@ref Introduction-to-PowerModelsONM)

## Optimizers

Although PowerModelsONM includes some open source solvers by default, namely

- NLP: [Ipopt.jl](https://github.com/jump-dev/Ipopt.jl)
- MIP: [Cbc.jl](https://github.com/jump-dev/Cbc.jl)
- MINLP: [Alpine.jl](https://github.com/lanl-ansi/Alpine.jl)
- MISOCP: [Juniper.jl](https://github.com/lanl-ansi/Juniper.jl)

we recommend using Gurobi to solve the [`optimal switching problem`](@ref optimize_switches!), if it is available to you, as we have found it has far superior performance on the MISOCP problem that it is solving as compared to the open-source solutions.

!!! info
    To use Gurobi with PowerModelsONM, do `import Gurobi` __BEFORE__ `import PowerModelsONM`. We use [Requires.jl](https://github.com/JuliaPackaging/Requires.jl) to manage the Gurobi Environment `GRB_ENV`, which will check out a license that can be used throughout the optimization solves.

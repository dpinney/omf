# PowerModelsONM.jl

```@meta
CurrentModule = PowerModelsONM
```

## What is PowerModelsONM?

[PowerModelsONM.jl](https://github.com/lanl-ansi/PowerModelsONM.jl) is a Julia/JuMP-based library for optimizing the operations of networked microgrids under contingencies, in particular unbalanced (i.e., multiconductor) power distribution networks.

## Resources for Getting Started

Read the [Installation Guide](@ref Installation-Guide)

Read the [Quickstart Guide](@ref Quick-Start-Guide)

Read the introductory tutorial [Introduction to PowerModelsONM](@ref Introduction-to-PowerModelsONM)

## How the documentation is structured

The following is a high-level overview of how our documetation is structured. There are three primary sections:

- The __Manual__ contains detailed documentation for certain aspects of PowerModelsONM, such as

- __Tutorials__ contains working examples of how to use PowerModelsONM. Start here if you are new to PowerModelsONM.

- The __API Reference__ contains a complete list of the functions you can use in PowerModelsONM. Look here if you want to know how to use a particular function.

## PowerModelsONM Analyses Packages

PowerModelsONM depends on several other PowerModels(...) packages from the InfrastructureModels ecosystem.

### PowerModelsDistribution

[PowerModelsDistribution.jl](https://github.com/lanl-ansi/PowerModelsDistribution.jl) is a Julia/JuMP-based package for modeling unbalanced (i.e., multiconductor) power networks. This is the primary modeling framework utilized in PowerModelsONM, and contains the primary logic for optimization and parsing of network data.

### PowerModelsProtection

[PowerModelsProtection.jl](https://github.com/lanl-ansi/PowerModelsProtection.jl) is a Julia/JuMP-based package for performing fault studies on both transmission (via extentions to [PowerModels.jl](https://github.com/lanl-ansi/PowerModels.jl)) and distribution (via extensions to [PowerModelsDistribution.jl](https://github.com/lanl-ansi/PowerModelsDistribution.jl)). In the future, the goal is to include optimal protection coordination formulations and constraints for optimal switching problems.

PowerModelsONM utilizes PowerModelsProtection to perform fault analysis after optimizing the switch configurations and dispatch by using an unbalanced IVR formuation.

### PowerModelsStability

[PowerModelsStability.jl](https://github.com/lanl-ansi/PowerModelsStability.jl) is a Julia/JuMP-based package for performing small signal stability analysis on distribution data sets (via extensions to [PowerModelsDistribution.jl](https://github.com/lanl-ansi/PowerModelsDistribution.jl)). Currently the capabilities of this tool are somewhat limited, as they are under active research and development; this capability is completely novel in this context. PowerModelsONM uses PowerModelsStability to report whether the resulting network configurations are small signal stable at each timestep.

## License

This code is provided under a BSD license as part of the Multi-Infrastructure Control and Optimization Toolkit (MICOT) project, LA-CC-13-108.

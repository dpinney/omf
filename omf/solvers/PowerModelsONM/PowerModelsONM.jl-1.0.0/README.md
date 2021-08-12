# PowerModelsONM

_An Optmization library for the operation and restoration of electric power distribution feeders featuring networked microgrids_

|                             __Documentation__                             |                               __Build Status__                                |
| :-----------------------------------------------------------------------: | :---------------------------------------------------------------------------: |
| [![][docs-stable-img]][docs-stable-url] [![][docs-dev-img]][docs-dev-url] | [![][github-actions-img]][github-actions-url] [![][codecov-img]][codecov-url] |

This package combines various packages in the [InfrastructureModels.jl](https://github.com/lanl-ansi/InfrastructureModels.jl) optimization library ecosystem, particularly those related to electric power distribution.

PowerModelsONM focuses on optimizing the operations and restoration of phase unbalanced (multiconductor) distribution feeders that feature multiple grid-forming generation assets such as solar PV, deisel generators, energy storage, etc. Phase unbalanced modeling is achieved using [PowerModelsDistribution](https://github.com/lanl-ansi/PowerModelsDistribution.jl). This library features a custom implementation of an optimal switching / load shedding (mld) problem. See [documentation][docs-stable-url] for more details.

## Installation

To install PowerModelsONM, use the built-in Julia package manager

```
pkg> add PowerModelsONM
```

Or, equivalently, via the `Pkg` API:

```julia
julia> import Pkg; Pkg.add("PowerModelsONM")
```

or to develop the package,

```julia
julia> import Pkg; Pkg.develop(Pkg.PackageSpec(; name="PowerModelsONM", url="https://github.com/lanl-ansi/PowerModelsONM.jl"))
```

## Questions and contributions

Usage questions can be posted on the [Github Discussions forum][discussions-url].

Contributions, feature requests, and suggestions are welcome; please open an [issue][issues-url] if you encounter any problems. The [contributing page][contrib-url] has guidelines that should be followed when opening pull requests and contributing code.

## License

This code is provided under a BSD license as part of the Multi-Infrastructure Control and Optimization Toolkit (MICOT) project, LA-CC-13-108.

[docs-dev-img]: https://github.com/lanl-ansi/PowerModelsONM.jl/workflows/Documentation/badge.svg
[docs-dev-url]: https://lanl-ansi.github.io/PowerModelsONM.jl/dev

[docs-stable-img]: https://github.com/lanl-ansi/PowerModelsONM.jl/workflows/Documentation/badge.svg
[docs-stable-url]: https://lanl-ansi.github.io/PowerModelsONM.jl/stable

[github-actions-img]: https://github.com/lanl-ansi/PowerModelsONM.jl/workflows/CI/badge.svg
[github-actions-url]: https://github.com/lanl-ansi/PowerModelsONM.jl/actions/workflows/ci.yml

[codecov-img]: https://codecov.io/gh/lanl-ansi/PowerModelsONM.jl/branch/main/graph/badge.svg
[codecov-url]: https://codecov.io/gh/lanl-ansi/PowerModelsONM.jl

[contrib-url]: https://lanl-ansi.github.io/PowerModelsONM.jl/stable/developer/contributing.html
[discussions-url]: https://github.com/lanl-ansi/PowerModelsONM.jl/discussions
[issues-url]: https://github.com/lanl-ansi/PowerModelsONM.jl/issues

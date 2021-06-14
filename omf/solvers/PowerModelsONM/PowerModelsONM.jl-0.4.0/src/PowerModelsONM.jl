module PowerModelsONM
    import InfrastructureModels
    import PowerModelsDistribution

    const PMD = PowerModelsDistribution

    import Ipopt
    import Cbc
    import Juniper

    try
        @eval import Gurobi
    catch err
        @warn "Gurobi.jl not installed."
    end

    import ArgParse

    import JSON
    import XLSX
    import DataFrames

    import Memento
    import Logging
    import LoggingExtras

    import Dates

    import LinearAlgebra: eigvals
    import Statistics: mean

    # Additional PowerModels{x} Services
    import PowerModelsProtection
    import PowerModelsStability

    function __init__()
        global _LOGGER = Memento.getlogger(PowerModelsDistribution._PM)
        try
            global GRB_ENV = Gurobi.Env()
        catch err
        end
    end

    include("core/common.jl")
    include("core/constraint_template.jl")
    include("core/constraint.jl")
    include("core/data.jl")
    include("core/objective.jl")
    include("core/ref.jl")
    include("core/solution.jl")
    include("core/statistics.jl")
    include("core/variable.jl")

    include("form/shared.jl")

    include("io/inputs.jl")
    include("io/outputs.jl")

    include("prob/common.jl")
    include("prob/osw_mld.jl")
    include("prob/osw.jl")

    include("app/main.jl")

    # Export must go last
    include("core/export.jl")
end # module

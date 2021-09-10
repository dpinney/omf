"""
    build_solver_instances!(args::Dict{String,<:Any})::Dict{String,Any}

Creates the Optimizers in-place (within the args dict data structure), for use inside [`entrypoint`](@ref entrypoint),
using [`build_solver_instances`](@ref build_solver_instances), assigning them to `args["solvers"]``
"""
function build_solver_instances!(args::Dict{String,<:Any})::Dict{String,Any}
    if !haskey(args, "solvers")
        args["solvers"] = Dict{String,Any}(
            "nlp_solver" => missing,
            "mip_solver" => missing,
            "minlp_solver" => missing,
            "misocp_solver" => missing,
        )
    end

    args["solvers"] = build_solver_instances(;
        nlp_solver = args["solvers"]["nlp_solver"],
        mip_solver = args["solvers"]["mip_solver"],
        minlp_solver = args["solvers"]["minlp_solver"],
        misocp_solver = args["solvers"]["misocp_solver"],
        nlp_solver_tol=get(get(args, "settings", Dict()), "nlp_solver_tol", 1e-4),
        mip_solver_tol=get(get(args, "settings", Dict()), "mip_solver_tol", 1e-4),
        verbose=get(args, "verbose", false),
        debug=get(args, "debug", false),
        gurobi=get(args, "gurobi", false)
    )
end


"""
    build_solver_instances(; nlp_solver=missing, nlp_solver_tol::Real=1e-4, mip_solver=missing, mip_solver_tol::Real=1e-4, minlp_solver=missing, misocp_solver=missing, gurobi::Bool=false, verbose::Bool=false, debug::Bool=false)::Dict{String,Any}

Returns solver instances as a Dict ready for use with JuMP Models, for NLP (`"nlp_solver"`), MIP (`"mip_solver"`), MINLP (`"minlp_solver"`), and (MI)SOC (`"misocp_solver"`) problems.

- `nlp_solver` (default: `missing`): If missing, will use Ipopt as NLP solver
- `nlp_solver_tol` (default: `1e-4`): The solver tolerance
- `mip_solver` (default: `missing`): If missing, will use Cbc as MIP solver, or Gurobi if `gurobi==true`
- `minlp_solver` (default: `missing`): If missing, will use Alpine with `nlp_solver` and `mip_solver`
- `misocp_solver` (default: `missing`): If missing will use Juniper with `mip_solver`, or Gurobi if `gurobi==true`
- `verbose` (default: `false`): Sets the verbosity of the solvers
- `debug` (default: `false`): Sets the verbosity of the solvers even higher (if available)
- `gurobi` (default: `false`): Use Gurobi for MIP / MISOC solvers
"""
function build_solver_instances(; nlp_solver=missing, nlp_solver_tol::Real=1e-4, mip_solver=missing, mip_solver_tol::Real=1e-4, minlp_solver=missing, misocp_solver=missing, gurobi::Bool=false, verbose::Bool=false, debug::Bool=false)::Dict{String,Any}
    if ismissing(nlp_solver)
        nlp_solver = optimizer_with_attributes(Ipopt.Optimizer, "tol"=>nlp_solver_tol, "print_level"=>verbose ? 3 : debug ? 5 : 0)
    end

    if ismissing(mip_solver)
        if gurobi
            mip_solver = optimizer_with_attributes(() -> Gurobi.Optimizer(GRB_ENV), "OutputFlag" => verbose || debug ? 1 : 0)
        else
            mip_solver = optimizer_with_attributes(Cbc.Optimizer, "logLevel" => verbose || debug ? 1 : 0)
        end
    end

    if ismissing(minlp_solver)
        minlp_solver = optimizer_with_attributes(Alpine.Optimizer, JuMP.MOI.Silent() => verbose || debug, "nlp_solver" => nlp_solver, "mip_solver" => mip_solver, "presolve_bt" => true, "presolve_bt_max_iter" => 5, "disc_ratio" => 12)
    end

    if ismissing(misocp_solver)
        if gurobi
            misocp_solver = optimizer_with_attributes(() -> Gurobi.Optimizer(GRB_ENV), "OutputFlag"=>verbose || debug ? 1 : 0, "NonConvex"=>2)
        else
            misocp_solver = optimizer_with_attributes(Juniper.Optimizer, "nl_solver" => nlp_solver, "mip_solver" => mip_solver, "log_levels"=>verbose ? [:Error,:Warn] : debug ? [:Error,:Warn,:Info] : [])
        end
    end

    return Dict{String,Any}("nlp_solver" => nlp_solver, "mip_solver" => mip_solver, "minlp_solver" => minlp_solver, "misocp_solver" => misocp_solver)
end

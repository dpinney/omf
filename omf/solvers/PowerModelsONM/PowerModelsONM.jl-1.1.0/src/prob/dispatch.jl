"""
    optimize_dispatch!(args::Dict{String,<:Any}; update_network_data::Bool=true, solver::String="nlp_solver")::Dict{String,Any}

Solves optimal dispatch problem in-place, for use in [`entrypoint`](@ref entrypoint), using [`optimize_dispatch`](@ref optimize_dispatch).
If you are using this to optimize after running [`optimize_switches!`](@ref optimize_switches!), this assumes that the correct
switch states from those results have already been propagated into `args["network"]`

If `update_network_data` (default: false) the results of the optimization will be automatically merged into
`args["network"]`.

`solver` (default: `"nlp_solver"`) specifies which solver to use for the OPF problem from `args["solvers"]`
"""
function optimize_dispatch!(args::Dict{String,<:Any}; update_network_data::Bool=false, solver::String=get(args, "opt-disp-solver", "nlp_solver"))::Dict{String,Any}
    args["opt-disp-formulation"] = _get_formulation(get(args, "opt-disp-formulation", "lindistflow"))

    if update_network_data
        args["network"] = apply_switch_solutions!(args["network"], get(args, "optimal_switching_results", Dict{String,Any}()))
    end

    args["optimal_dispatch_result"] = optimize_dispatch(args["network"], args["opt-disp-formulation"], args["solvers"][solver]; switching_solutions=get(args, "optimal_switching_results", missing))

    update_network_data && PMD._IM.update_data!(args["network"], get(args["optimal_dispatch_result"], "solution", Dict{String, Any}()))

    return args["optimal_dispatch_result"]
end


"""
    optimize_dispatch(network::Dict{String,<:Any}, formulation::Type, solver)::Dict{String,Any}

Solve a multinetwork optimal power flow (`solve_mn_mc_opf`) using `formulation` and `solver`
"""
function optimize_dispatch(network::Dict{String,<:Any}, formulation::Type, solver; switching_solutions::Union{Missing,Dict{String,<:Any}}=missing)::Dict{String,Any}
    data = _prepare_dispatch_data(network, switching_solutions)

    @info "running optimal dispatch with $(formulation)"
    PMD.solve_mn_mc_opf(data, formulation, solver; solution_processors=[PMD.sol_data_model!])
end


"prepares data for running a optimal dispatch problem, copying in solutions from the switching results, if present"
function _prepare_dispatch_data(network::T, switching_solutions::Union{Missing,T})::T where T <: Dict{String,<:Any}
    data = deepcopy(network)

    if !ismissing(switching_solutions)
        for (n, results) in switching_solutions
            nw = get(results, "solution", Dict())

            for (i,switch) in get(nw, "switch", Dict{String,Any}())
                if haskey(switch, "state")
                    data["nw"]["$n"]["switch"][i]["state"] = switch["state"]
                end
            end

            for type in ["bus", "load", "shunt", "generator", "solar", "voltage_source", "storage"]
                for (i,obj) in get(nw, type, Dict{String,Any}())
                    if round(Int, get(obj, "status", 1)) != 1
                        data["nw"]["$n"][type][i]["status"] = PMD.DISABLED
                    end
                end
            end
        end
    end

    return data
end

"""
    optimize_dispatch!(args::Dict{String,<:Any}; update_network_data::Bool=true, solver::String="nlp_solver")::Dict{String,Any}

Solves optimal dispatch problem in-place, for use in [`entrypoint`](@ref entrypoint), using [`optimize_dispatch`](@ref optimize_dispatch).
If you are using this to optimize after running [`optimize_switches!`](@ref optimize_switches!), this assumes that the correct
switch states from those results have already been propagated into `args["network"]`

If `update_network_data` (default: true) the results of the optimization will be automatically merged into
`args["network"]`.

`solver` (default: `"nlp_solver"`) specifies which solver to use for the OPF problem from `args["solvers"]`
"""
function optimize_dispatch!(args::Dict{String,<:Any}; update_network_data::Bool=true, solver::String="nlp_solver")::Dict{String,Any}
    args["opt-disp-formulation"] = _get_formulation(get(args, "opt-disp-formulation", "lindistflow"))

    args["network"] = apply_switch_solutions!(args["network"], get(args, "optimal_switching_results", Dict{String,Any}()))

    args["optimal_dispatch_result"] = optimize_dispatch(args["network"], args["opt-disp-formulation"], args["solvers"][solver])

    update_network_data && PMD._IM.update_data!(args["network"], get(args["optimal_dispatch_result"], "solution", Dict{String, Any}()))

    return args["optimal_dispatch_result"]
end


"""
    optimize_dispatch(network::Dict{String,<:Any}, formulation::Type, solver)::Dict{String,Any}

Solve a multinetwork optimal power flow (`solve_mn_mc_opf`) using `formulation` and `solver`
"""
function optimize_dispatch(network::Dict{String,<:Any}, formulation::Type, solver)::Dict{String,Any}
    @info "running optimal dispatch with $(formulation)"
    PMD.solve_mn_mc_opf(network, formulation, solver; solution_processors=[PMD.sol_data_model!])
end

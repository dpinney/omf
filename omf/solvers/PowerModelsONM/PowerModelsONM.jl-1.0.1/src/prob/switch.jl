"""
    optimize_switches!(args::Dict{String,<:Any})::Dict{String,Any}

Optimizes switch states (therefore shedding load or not) in-place, for use in [`entrypoint`](@ref entrypoint),
using [`optimize_switches`]

Uses LPUBFDiagPowerModel (LinDist3Flow), and therefore requires `args["solvers"]["misocp_solver"]` to be specified
"""
function optimize_switches!(args::Dict{String,<:Any})::Dict{String,Any}
    args["optimal_switching_results"] = optimize_switches(args["network"], args["solvers"]["misocp_solver"]; gurobi=get(args, "gurobi", false))
end


"""
    optimize_switches(network::Dict{String,<:Any}, solver; gurobi::Bool=false)::Dict{String,Any}

Iterates over all subnetworks in a multinetwork data structure `network`, in order, and solves
the optimal switching / MLD problem sequentially, updating the next timestep with the new switch
configurations and storage energies from the solved timestep.
"""
function optimize_switches(network::Dict{String,<:Any}, solver; gurobi::Bool=false)::Dict{String,Any}
    mn_data = _prepare_optimal_switching_data(network)

    results = Dict{String,Any}()
    ns = sort([parse(Int, i) for i in keys(mn_data["nw"])])
    @showprogress length(ns) "Running switch optimization (mld)... " for n in ns
        if haskey(results, "$(n-1)") && haskey(results["$(n-1)"], "solution")
            _update_switch_settings!(mn_data["nw"]["$n"], results["$(n-1)"]["solution"])
            _update_storage_capacity!(mn_data["nw"]["$n"], results["$(n-1)"]["solution"])
        end

        prob = gurobi ? solve_mc_osw_mld_mi_indicator : solve_mc_osw_mld_mi

        results["$n"] = optimize_switches(mn_data["nw"]["$n"], prob, solver)

        if haskey(results["$n"], "solution")
            _update_switch_settings!(mn_data["nw"]["$n"], results["$n"]["solution"])
        end
    end

    return results
end


"""
    optimize_switches(subnetwork::Dict{String,<:Any}, prob::Function, solver; formulation=PMD.LPUBFDiagPowerModel)::Dict{String,Any}

Optimizes switch states for load shedding on a single subnetwork (not a multinetwork), using `prob` ([`solve_mc_osw_mld_mi_indicator`](@ref solve_mc_osw_mld_mi_indicator),
if you are using a solver that supports indicator constraints like Gurobi or CPLEX, or [`solve_mc_osw_mld_mi`](@ref solve_mc_osw_mld_mi)), `solver`.

Optionally, a PowerModelsDistribution `formulation` can be set independently, but is LinDist3Flow by default.
"""
function optimize_switches(subnetwork::Dict{String,<:Any}, prob::Function, solver; formulation=PMD.LPUBFDiagPowerModel)::Dict{String,Any}
    prob(
        subnetwork,
        formulation,
        solver;
        solution_processors=[PMD.sol_data_model!],
        ref_extensions=[ref_add_load_blocks!, ref_add_max_switch_actions!],
        eng2math_passthrough=Dict{String,Vector{String}}("root"=>String["max_switch_actions"])
    )
end


"helper function to prepare optimal switching data structure"
function _prepare_optimal_switching_data(network::Dict{String,<:Any})::Dict{String,Any}
    mn_data = deepcopy(network)
    for (n,nw) in mn_data["nw"]
        nw["data_model"] = mn_data["data_model"]
    end

    return mn_data
end

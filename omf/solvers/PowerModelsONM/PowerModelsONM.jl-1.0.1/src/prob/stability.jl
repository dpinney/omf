"""
    run_stability_analysis!(args::Dict{String,<:Any}; validate::Bool=true, formulation::Type=PMD.ACRUPowerModel, solver::String="nlp_solver")::Dict{String,Bool}

Runs small signal stability analysis using PowerModelsStability and determines if each timestep configuration is stable,
in-place, storing the results in `args["stability_results"]`, for use in [`entrypoint`](@ref entrypoint), Uses
[`run_stability_analysis`](@ref run_stability_analysis)

If `validate`, raw inverters data will be validated against JSON schema

The formulation can be specified with `formulation`, but note that it must result in `"vm"` and `"va"` variables in the
solution, or else `PowerModelsDistribution.sol_data_model!` must support converting the voltage variables into
polar coordinates.

`solver` (default: `"nlp_solver"`) specifies which solver in `args["solvers"]` to use for the stability analysis (NLP OPF)
"""
function run_stability_analysis!(args::Dict{String,<:Any}; validate::Bool=true, formulation::Type=PMD.ACRUPowerModel, solver::String="nlp_solver")::Dict{String,Bool}
    if !isempty(get(args, "inverters", ""))
        if isa(args["inverters"], String)
            args["inverters"] = parse_inverters(args["inverters"]; validate=validate)
        end
    else
        # TODO what to do if no inverters are defined?
        args["inverters"] = Dict{String,Any}(
            "omega0" => 376.9911,
            "rN" => 1000,
        )
    end

    args["stability_results"] = run_stability_analysis(args["network"], args["inverters"], args["solvers"][solver]; formulation=formulation)
end


"""
    run_stability_analysis(network, inverters::Dict{String,<:Any}, solver; formulation::Type=PMD.ACRUPowerModel)::Dict{String,Bool}

Runs small signal stability analysis using PowerModelsStability and determines if each timestep configuration is stable

`inverters` is an already parsed inverters file using [`parse_inverters`](@ref parse_inverters)

The formulation can be specified with `formulation`, but note that it must result in `"vm"` and `"va"` variables in the
solution, or else `PowerModelsDistribution.sol_data_model!` must support converting the voltage variables into
polar coordinates.

`solver` for stability analysis (NLP OPF)
"""
function run_stability_analysis(network, inverters::Dict{String,<:Any}, solver; formulation::Type=PMD.ACRUPowerModel)::Dict{String,Bool}
    mn_data = _prepare_stability_multinetwork_data(network, inverters)

    is_stable = Dict{String,Bool}()
    ns = sort([parse(Int, i) for i in keys(mn_data["nw"])])
    @showprogress length(ns) "Running stability analysis... " for n in ns
        is_stable["$n"] = run_stability_analysis(mn_data["nw"]["$n"], inverters["omega0"], inverters["rN"], solver; formulation=formulation)
    end

    return is_stable
end


"""
    run_stability_analysis(subnetwork::Dict{String,<:Any}, omega0::Real, rN::Int, solver; formulation::Type=PMD.ACRUPowerModel)::Bool

Runs stability analysis on a single subnetwork (not a multinetwork) using a nonlinear `solver`.
"""
function run_stability_analysis(subnetwork::Dict{String,<:Any}, omega0::Real, rN::Int, solver; formulation::Type=PMD.ACRUPowerModel)::Bool
    math_model = PowerModelsStability.transform_data_model(subnetwork)
    opf_solution = PowerModelsStability.solve_mc_opf(math_model, formulation, solver; solution_processors=[PMD.sol_data_model!])

    Atot = PowerModelsStability.obtainGlobal_multi(math_model, opf_solution, omega0, rN)
    eigValList = eigvals(Atot)
    statusTemp = true
    for eig in eigValList
        if eig.re > 0
            statusTemp = false
        end
    end

    return statusTemp
end


"helper function to prepare the multinetwork data for stability analysis (adds inverters, data_model)"
function _prepare_stability_multinetwork_data(network::Dict{String,<:Any}, inverters::Dict{String,<:Any})::Dict{String,Any}
    mn_data = deepcopy(network)

    for (n, nw) in mn_data["nw"]
        nw["data_model"] = mn_data["data_model"]
        PowerModelsStability.add_inverters!(nw, inverters)
    end

    return mn_data
end

"""
    solve_mn_mc_osw_mld_mi_indicator(data::Union{Dict{String,<:Any}, String}, model_type::Type, solver; kwargs...)::Dict{String,Any}

Solves a __multinetwork__ multiconductor optimal switching (mixed-integer) problem using `model_type` and `solver`

Uses [indicator constraints](https://jump.dev/JuMP.jl/stable/manual/constraints/#Indicator-constraints), so
requires a solver that supports them (e.g., Gurobi or CPLEX)

Calls back to PowerModelsDistribution.solve_mc_model, and therefore will accept any valid `kwargs`
for that function. See PowerModelsDistribution [documentation](https://lanl-ansi.github.io/PowerModelsDistribution.jl/latest)
for more details.
"""
function solve_mn_mc_osw_mld_mi_indicator(data::Union{Dict{String,<:Any}, String}, model_type::Type, solver; kwargs...)::Dict{String,Any}
    return PMD.solve_mc_model(data, model_type, solver, _build_mn_mc_osw_mld_mi_indicator; multinetwork=true, kwargs...)
end


"Multinetwork load shedding problem for Branch Flow model"
function _build_mn_mc_osw_mld_mi_indicator(pm::PMD.AbstractUBFModels)
    for (n, network) in PMD.nws(pm)
        PMD.variable_mc_branch_current(pm; nw=n)
        PMD.variable_mc_branch_power(pm; nw=n)
        PMD.variable_mc_switch_power(pm; nw=n)
        PMD.variable_mc_switch_state(pm; nw=n, relax=false)
        PMD.variable_mc_transformer_power(pm; nw=n)
        PMD.variable_mc_generator_power(pm; nw=n)
        PMD.variable_mc_bus_voltage(pm; nw=n)

        PMD.variable_mc_load_indicator(pm; nw=n, relax=true)
        PMD.variable_mc_shunt_indicator(pm; nw=n, relax=true)
        PMD.variable_mc_storage_power_mi(pm; nw=n, relax=true)

        PMD.constraint_mc_model_current(pm; nw=n)

        for i in PMD.ids(pm, n, :ref_buses)
            PMD.constraint_mc_theta_ref(pm, i; nw=n)
        end

        for i in PMD.ids(pm, n, :gen)
            PMD.constraint_mc_generator_power(pm, i; nw=n)
        end

        for i in PMD.ids(pm, n, :bus)
            PMD.constraint_mc_power_balance_shed(pm, i; nw=n)
        end

        for i in PMD.ids(pm, n, :storage)
            PMD.constraint_mc_storage_losses(pm, i; nw=n)
            # PMD.constraint_mc_storage_thermal_limit(pm, i; nw=n)
            PMD.constraint_storage_complementarity_mi(pm, i; nw=n)
        end

        for i in PMD.ids(pm, n, :branch)
            PMD.constraint_mc_power_losses(pm, i; nw=n)

            PMD.constraint_mc_model_voltage_magnitude_difference(pm, i; nw=n)
            PMD.constraint_mc_voltage_angle_difference(pm, i; nw=n)

            PMD.constraint_mc_thermal_limit_from(pm, i; nw=n)
            PMD.constraint_mc_thermal_limit_to(pm, i; nw=n)
        end

        for i in PMD.ids(pm, n, :switch)
            PMD.constraint_mc_switch_state_on_off(pm, i; nw=n, relax=true)
            PMD.constraint_mc_switch_thermal_limit(pm, i)
        end

        for i in PMD.ids(pm, n, :transformer)
            PMD.constraint_mc_transformer_power(pm, i; nw=n)
        end
    end

    network_ids = sort(collect(PMD.nw_ids(pm)))

    n_1 = network_ids[1]

    for i in PMD.ids(pm, :storage; nw=n_1)
        PMD.constraint_storage_state(pm, i; nw=n_1)
    end

    for n_2 in network_ids[2:end]
        for i in PMD.ids(pm, :storage; nw=n_2)
            PMD.constraint_storage_state(pm, i, n_1, n_2)
        end

        n_1 = n_2
    end

    PMD.objective_mc_min_load_setpoint_delta_simple_switch(pm)
end


"""
    solve_mc_osw_mld_mi_indicator(data::Union{Dict{String,<:Any}, String}, model_type::Type, solver; kwargs...)::Dict{String,Any}

Solves a multiconductor optimal switching (mixed-integer) problem using `model_type` and `solver`

Uses [indicator constraints](https://jump.dev/JuMP.jl/stable/manual/constraints/#Indicator-constraints), so
requires a solver that supports them (e.g., Gurobi or CPLEX)

Calls back to PowerModelsDistribution.solve_mc_model, and therefore will accept any valid `kwargs`
for that function. See PowerModelsDistribution [documentation](https://lanl-ansi.github.io/PowerModelsDistribution.jl/latest)
for more details.
"""
function solve_mc_osw_mld_mi_indicator(data::Union{Dict{String,<:Any}, String}, model_type::Type, solver; kwargs...)::Dict{String,Any}
    return PMD.solve_mc_model(data, model_type, solver, _build_mc_osw_mld_mi_indicator; multinetwork=false, kwargs...)
end


"Multinetwork load shedding problem for Branch Flow model"
function _build_mc_osw_mld_mi_indicator(pm::PMD.AbstractUBFModels)
    PMD.variable_mc_bus_voltage_indicator(pm; relax=false)
    PMD.variable_mc_bus_voltage_on_off(pm)

    PMD.variable_mc_branch_current(pm)
    PMD.variable_mc_branch_power(pm)
    PMD.variable_mc_switch_power(pm)
    PMD.variable_mc_switch_state(pm; relax=false)
    PMD.variable_mc_transformer_power(pm)

    PMD.variable_mc_gen_indicator(pm; relax=false)
    PMD.variable_mc_generator_power_on_off(pm)

    PMD.variable_mc_storage_indicator(pm, relax=false)
    PMD.variable_mc_storage_power_mi_on_off(pm, relax=false)

    variable_mc_load_block_indicator(pm; relax=false)
    PMD.variable_mc_shunt_indicator(pm; relax=false)

    PMD.constraint_mc_model_current(pm)

    for i in PMD.ids(pm, :ref_buses)
        PMD.constraint_mc_theta_ref(pm, i)
    end

    PMD.constraint_mc_bus_voltage_on_off(pm)

    for i in PMD.ids(pm, :gen)
        PMD.constraint_mc_gen_power_on_off(pm, i)
    end

    for i in PMD.ids(pm, :bus)
        PMD.constraint_mc_power_balance_shed(pm, i)
    end

    for i in PMD.ids(pm, :storage)
        PMD.constraint_storage_state(pm, i)
        PMD.constraint_storage_complementarity_mi(pm, i)
        PMD.constraint_mc_storage_on_off(pm, i)
        PMD.constraint_mc_storage_losses(pm, i)
        PMD.constraint_mc_storage_thermal_limit(pm, i)
    end

    for i in PMD.ids(pm, :branch)
        PMD.constraint_mc_power_losses(pm, i)
        PMD.constraint_mc_model_voltage_magnitude_difference(pm, i)

        PMD.constraint_mc_voltage_angle_difference(pm, i)

        PMD.constraint_mc_thermal_limit_from(pm, i)
        PMD.constraint_mc_thermal_limit_to(pm, i)
    end

    constraint_switch_state_max_actions(pm)
    # constraint_load_block_isolation(pm; relax=false)
    for i in PMD.ids(pm, :switch)
        PMD.constraint_mc_switch_state_on_off(pm, i; relax=false)
        PMD.constraint_mc_switch_thermal_limit(pm, i)
    end

    for i in PMD.ids(pm, :transformer)
        PMD.constraint_mc_transformer_power(pm, i)
    end

    objective_mc_min_load_setpoint_delta_switch(pm)
end


"""
    solve_mc_osw_mld_mi(data::Union{Dict{String,<:Any}, String}, model_type::Type, solver; kwargs...)::Dict{String,Any}

Solves a multiconductor optimal switching (relaxed, i.e., _not_ mixed-integer) problem using `model_type` and `solver`

Calls back to PowerModelsDistribution.solve_mc_model, and therefore will accept any valid `kwargs`
for that function. See PowerModelsDistribution [documentation](https://lanl-ansi.github.io/PowerModelsDistribution.jl/latest)
for more details.
"""
function solve_mc_osw_mld_mi(data::Union{Dict{String,<:Any}, String}, model_type::Type, solver; kwargs...)::Dict{String,Any}
    return PMD.solve_mc_model(data, model_type, solver, _build_mc_osw_mld_mi; multinetwork=false, kwargs...)
end


"Multinetwork load shedding problem for Branch Flow model"
function _build_mc_osw_mld_mi(pm::PMD.AbstractUBFModels)
    PMD.variable_mc_bus_voltage_indicator(pm; relax=false)
    PMD.variable_mc_bus_voltage_on_off(pm)

    PMD.variable_mc_branch_current(pm)
    PMD.variable_mc_branch_power(pm)
    PMD.variable_mc_switch_power(pm)
    PMD.variable_mc_switch_state(pm; relax=false)
    PMD.variable_mc_transformer_power(pm)

    PMD.variable_mc_gen_indicator(pm; relax=false)
    PMD.variable_mc_generator_power_on_off(pm)

    PMD.variable_mc_storage_indicator(pm, relax=false)
    PMD.variable_mc_storage_power_mi_on_off(pm, relax=false)

    variable_mc_load_block_indicator(pm; relax=false)
    PMD.variable_mc_shunt_indicator(pm; relax=false)

    PMD.constraint_mc_model_current(pm)

    for i in PMD.ids(pm, :ref_buses)
        PMD.constraint_mc_theta_ref(pm, i)
    end

    PMD.constraint_mc_bus_voltage_on_off(pm)

    for i in PMD.ids(pm, :gen)
        PMD.constraint_mc_gen_power_on_off(pm, i)
    end

    for i in PMD.ids(pm, :bus)
        PMD.constraint_mc_power_balance_shed(pm, i)
    end

    for i in PMD.ids(pm, :storage)
        PMD.constraint_storage_state(pm, i)
        PMD.constraint_storage_complementarity_mi(pm, i)
        PMD.constraint_mc_storage_on_off(pm, i)
        PMD.constraint_mc_storage_losses(pm, i)
        PMD.constraint_mc_storage_thermal_limit(pm, i)
    end

    for i in PMD.ids(pm, :branch)
        PMD.constraint_mc_power_losses(pm, i)
        PMD.constraint_mc_model_voltage_magnitude_difference(pm, i)

        PMD.constraint_mc_voltage_angle_difference(pm, i)

        PMD.constraint_mc_thermal_limit_from(pm, i)
        PMD.constraint_mc_thermal_limit_to(pm, i)
    end

    constraint_switch_state_max_actions(pm)
    constraint_load_block_isolation(pm; relax=true)
    for i in PMD.ids(pm, :switch)
        PMD.constraint_mc_switch_state_on_off(pm, i; relax=true)
        PMD.constraint_mc_switch_thermal_limit(pm, i)
    end

    for i in PMD.ids(pm, :transformer)
        PMD.constraint_mc_transformer_power(pm, i)
    end

    objective_mc_min_load_setpoint_delta_switch(pm)
end

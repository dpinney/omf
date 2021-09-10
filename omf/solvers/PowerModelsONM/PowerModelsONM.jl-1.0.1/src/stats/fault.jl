"""
    get_timestep_fault_currents!(args::Dict{String,<:Any})::Vector{Dict{String,Any}}

Gets fault currents for switches and corresponding fault from study in-place in args, for use in [`entrypoint`](@ref entrypoint),
using [`get_timestep_fault_currents`](@ref get_timestep_fault_currents).
"""
function get_timestep_fault_currents!(args::Dict{String,<:Any})::Vector{Dict{String,Any}}
    args["output_data"]["Fault currents"] = get_timestep_fault_currents(get(args, "fault_studies_results", Dict{String,Any}()), get(args, "faults", Dict{String,Any}()), args["network"])
end


"""
    get_timestep_fault_currents(fault_studies_results::Dict{String,<:Any}, faults::Dict{String,<:Any}, network::Dict{String,<:Any})::Vector{Dict{String,Any}}

Gets information about the results of fault studies at each timestep, including:

- information about the fault, such as
  - the admittance (`"conductance (S)"` and `"susceptance (S)"`),
  - the bus at which the fault is applied
  - the type of fault (3p, 3pg, llg, ll, lg), and
  - to which connections the fault applies
- information about the state at the network's protection, including
  - the fault current `|I| (A)`
  - the zero-sequence fault current `|I0| (A)`
  - the positive-sequence fault current `|I1| (A)`
  - the negative-sequence fault current `|I2| (A)`
  - the bus voltage from the from-side of the switch `|V| (V)`
"""
function get_timestep_fault_currents(fault_studies_results::Dict{String,<:Any}, faults::Dict{String,<:Any}, network::Dict{String,<:Any})::Vector{Dict{String,Any}}
    fault_currents = Dict{String,Any}[]

    for n in sort([parse(Int, i) for i in keys(fault_studies_results)])
        _fault_currents = Dict{String,Any}()
        for (bus_id, fault_types) in fault_studies_results["$n"]
            for (fault_type, sub_faults) in fault_types
                for (fault_id, fault_result) in sub_faults
                    fault = faults[bus_id][fault_type][fault_id]
                    if !isempty(get(fault_result, "solution", Dict()))
                        _fault_currents["$(bus_id)_$(fault_type)_$(fault_id)"] = Dict{String,Any}(
                            "fault" => Dict{String,Any}(
                                "bus" => fault["bus"],
                                "type" => fault["fault_type"],
                                "conductance (S)" => fault["g"],
                                "susceptance (S)" => fault["b"],
                                "connections" => fault["connections"],
                            ),
                            "switch" => Dict{String,Any}(
                                id => Dict{String,Any}(
                                    "|I| (A)" => haskey(switch, "crsw_fr") && haskey(switch, "cisw_fr") ? sqrt.(switch["crsw_fr"].^2 + switch["cisw_fr"].^2) : missing,
                                    "|I0| (A)" => haskey(switch, "cf0r_fr") && haskey(switch, "cf0i_fr") ? sqrt(switch["cf0r_fr"]^2+switch["cf0i_fr"]^2) : missing,
                                    "|I1| (A)" => haskey(switch, "cf1r_fr") && haskey(switch, "cf1i_fr") ? sqrt(switch["cf1r_fr"]^2+switch["cf1i_fr"]^2) : missing,
                                    "|I2| (A)" => haskey(switch, "cf2r_fr") && haskey(switch, "cf2i_fr") ? sqrt(switch["cf2r_fr"]^2+switch["cf2i_fr"]^2) : missing,
                                    # TODO add real and imaginary sequence currents
                                    "|V| (V)" => all(haskey(fault_result["solution"]["bus"][network["nw"]["$n"]["switch"][id]["f_bus"]], k) for k in ["vr", "vi"]) ? sqrt.(fault_result["solution"]["bus"][network["nw"]["$n"]["switch"][id]["f_bus"]]["vr"].^2+fault_result["solution"]["bus"][network["nw"]["$n"]["switch"][id]["f_bus"]]["vi"].^2) : missing
                                ) for (id, switch) in get(fault_result["solution"], "switch", Dict())
                            ),
                        )
                    end
                end
            end
        end
        push!(fault_currents, _fault_currents)
    end

    return fault_currents
end

"""
    parse_inverters(inverter_file::String; validate::Bool=true)::Dict{String,Any}

Parses an inverters JSON file, used in [`run_stability_analysis!`](@ref run_stability_analysis!)

## Validation

If `validate=true` (default), the parsed data structure will be validated against the latest [Inverters Schema](@ref Inverters-Schema).
"""
function parse_inverters(inverter_file::String; validate::Bool=true)::Dict{String,Any}
    inverters = PowerModelsStability.parse_json(inverter_file)

    if validate && !validate_inverters(inverters)
        error("'inverters' file could not be validated")
    end

    return inverters
end

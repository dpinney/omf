"""
    parse_network!(args::Dict{String,<:Any})::Dict{String,Any}

In-place version of [`parse_network`](@ref parse_network), returns the ENGINEERING multinetwork
data structure, which is available in `args` under `args["network"]`, and adds the non-expanded ENGINEERING
data structure under `args["base_network"]`
"""
function parse_network!(args::Dict{String,<:Any})::Dict{String,Any}
    if isa(args["network"], String)
        args["base_network"], args["network"] = parse_network(args["network"])
    end

    return args["network"]
end


"""
    parse_network(network_file::String)::Tuple{Dict{String,Any},Dict{String,Any}}

Parses network file given by runtime arguments into its base network, i.e., not expanded into a multinetwork,
and multinetwork, which is the multinetwork `ENGINEERING` representation of the network.
"""
function parse_network(network_file::String)::Tuple{Dict{String,Any},Dict{String,Any}}
    eng = PMD.parse_file(network_file; dss2eng_extensions=[PowerModelsProtection._dss2eng_solar_dynamics!, PowerModelsProtection._dss2eng_gen_dynamics!], transformations=[PMD.apply_kron_reduction!])

    mn_eng = PMD.make_multinetwork(eng)

    return eng, mn_eng
end

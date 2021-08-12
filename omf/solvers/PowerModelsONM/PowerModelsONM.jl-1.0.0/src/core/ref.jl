"Ref extension to add load blocks to ref"
function _ref_add_load_blocks!(ref::Dict{Symbol,<:Any}, data::Dict{String,<:Any})
    ref[:load_blocks] = Dict{Int,Set}(i => block for (i,block) in enumerate(PMD.identify_load_blocks(data)))

    load_block_map = Dict{Int,Int}()
    for (l,load) in get(data, "load", Dict())
        for (b,block) in ref[:load_blocks]
            if load["load_bus"] in block
                load_block_map[parse(Int,l)] = b
            end
        end
    end
    ref[:load_block_map] = load_block_map

    load_block_switches = Dict{Int,Vector{Int}}(b => Vector{Int}([]) for (b, block) in ref[:load_blocks])
    for (b,block) in ref[:load_blocks]
        for (s,switch) in get(data, "switch", Dict())
            if switch["f_bus"] in block || switch["t_bus"] in block
                if switch["dispatchable"] == 1 && switch["status"] == 1
                    push!(load_block_switches[b], parse(Int,s))
                end
            end
        end
    end
    ref[:load_block_switches] = load_block_switches
end


"""
    ref_add_load_blocks!(ref::Dict{Symbol,<:Any}, data::Dict{String,<:Any})

Ref extension to add load blocks to ref
"""
function ref_add_load_blocks!(ref::Dict{Symbol,<:Any}, data::Dict{String,<:Any})
    PMD.apply_pmd!(_ref_add_load_blocks!, ref, data; apply_to_subnetworks=true)
end

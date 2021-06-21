""
function ref_add_load_blocks!(ref::Dict{Symbol,<:Any}, data::Dict{String,<:Any})
    for (nw, nw_ref) in ref[:nw]
        nw_ref[:load_blocks] = Dict{Int,Set}(i => block for (i,block) in enumerate(identify_load_blocks(data; edges=["transformer", "branch"])))

        load_block_map = Dict{Int,Int}()
        for (l,load) in get(data, "load", Dict())
            for (b,block) in nw_ref[:load_blocks]
                if load["load_bus"] in block
                    load_block_map[parse(Int,l)] = b
                end
            end
        end
        nw_ref[:load_block_map] = load_block_map

        load_block_switches = Dict{Int,Vector{Int}}(b => Vector{Int}([]) for (b, block) in nw_ref[:load_blocks])
        for (b,block) in nw_ref[:load_blocks]
            for (s,switch) in get(data, "switch", Dict())
                if switch["f_bus"] in block || switch["t_bus"] in block
                    push!(load_block_switches[b], parse(Int,s))
                end
            end
        end
        nw_ref[:load_block_switches] = load_block_switches
    end
end

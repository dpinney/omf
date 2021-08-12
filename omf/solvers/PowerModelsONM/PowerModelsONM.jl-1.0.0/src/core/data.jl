"""
    identify_cold_loads(data::Dict)::Dict{String,Bool}

Identifies whether loads are currently "cold" or not using [`are_blocks_warm`](@ref are_blocks_warm)
"""
function identify_cold_loads(data::Dict{String,<:Any})::Dict{String,Bool}
    blocks = PMD.identify_load_blocks(data)
    is_warm = are_blocks_warm(data, blocks)

    load2block_map = Dict()
    for (l,load) in get(data, "load", Dict())
        for block in blocks
            if load["load_bus"] in block
                load2block_map[parse(Int,l)] = block
                break
            end
        end
    end

    return Dict{String,Bool}("$l" => !is_warm[block] for (l,block) in load2block_map)
end


"""
    are_blocks_warm(data::Dict{String,<:Any}, blocks)::Dict{Set,Bool}

Identifies whether load `blocks`, which is a set of set of buses, are "warm" or not using [`is_block_warm`](@ref is_block_warm)
"""
function are_blocks_warm(data::Dict{String,<:Any}, blocks)::Dict{Set,Bool}
    active_gen_buses = Set([gen["gen_bus"] for (_,gen) in get(data, "gen", Dict()) if gen[PMD.pmd_math_component_status["gen"]] != PMD.pmd_math_component_status_inactive["gen"]])
    active_storage_buses = Set([strg["storage_bus"] for (_,strg) in get(data, "storage", Dict()) if strg[PMD.pmd_math_component_status["storage"]] != PMD.pmd_math_component_status_inactive["storage"]])

    is_warm = Dict{Set,Bool}(block => false for block in blocks)
    for block in blocks
        for bus in block
            if bus in active_gen_buses || bus in active_storage_buses
                is_warm[block] = true
                break
            end
        end
    end
    return is_warm
end


"""
    is_block_warm(data::Dict, block::Set)::Bool

Returns true if a load `block` is "warm", i.e., has an active generation element within the block
"""
function is_block_warm(data::Dict{String,<:Any}, block::Set)::Bool
    active_gen_buses = Set([gen["gen_bus"] for (_,gen) in get(data, "gen", Dict()) if gen[PMD.pmd_math_component_status["gen"]] != PMD.pmd_math_component_status_inactive["gen"]])
    active_storage_buses = Set([strg["storage_bus"] for (_,strg) in get(data, "storage", Dict()) if strg[PMD.pmd_math_component_status["storage"]] != PMD.pmd_math_component_status_inactive["storage"]])

    for bus in block
        if bus in active_gen_buses || bus in active_storage_buses
            return true
            break
        end
    end
    return false
end

"Ref extension to add load blocks to ref"
function _ref_add_load_blocks!(ref::Dict{Symbol,<:Any}, data::Dict{String,<:Any})
    ref[:blocks] = Dict{Int,Set}(i => block for (i,block) in enumerate(PMD.identify_load_blocks(data)))
    ref[:bus_block_map] = Dict{Int,Int}(bus => b for (b,block) in ref[:blocks] for bus in block)
    ref[:block_loads] = Dict{Int,Set}(i => Set{Int}() for (i,_) in ref[:blocks])
    ref[:block_weights] = Dict{Int,Real}(i => 0.0 for (i,_) in ref[:blocks])
    ref[:block_shunts] = Dict{Int,Set{Int}}(i => Set{Int}() for (i,_) in ref[:blocks])
    ref[:block_gens] = Dict{Int,Set{Int}}(i => Set{Int}() for (i,_) in ref[:blocks])
    ref[:block_storages] = Dict{Int,Set{Int}}(i => Set{Int}() for (i,_) in ref[:blocks])

    for (l,load) in ref[:load]
        push!(ref[:block_loads][ref[:bus_block_map][load["load_bus"]]], l)
        ref[:block_weights][ref[:bus_block_map][load["load_bus"]]] += sum(abs.(load["pd"])) + sum(abs.(load["qd"])) + get(load, "priority", 0)
    end
    ref[:load_block_map] = Dict{Int,Int}(load => b for (b,block_loads) in ref[:block_loads] for load in block_loads)

    for (s,shunt) in ref[:shunt]
        push!(ref[:block_shunts][ref[:bus_block_map][shunt["shunt_bus"]]], s)
    end
    ref[:shunt_block_map] = Dict{Int,Int}(shunt => b for (b,block_shunts) in ref[:block_shunts] for shunt in block_shunts)

    for (g,gen) in ref[:gen]
        push!(ref[:block_gens][ref[:bus_block_map][gen["gen_bus"]]], g)
    end
    ref[:gen_block_map] = Dict{Int,Int}(gen => b for (b,block_gens) in ref[:block_gens] for gen in block_gens)

    for (s,strg) in ref[:storage]
        push!(ref[:block_storages][ref[:bus_block_map][strg["storage_bus"]]], s)
    end
    ref[:storage_block_map] = Dict{Int,Int}(strg => b for (b,block_storages) in ref[:block_storages] for strg in block_storages)

    ref[:block_graph] = LightGraphs.SimpleGraph(length(ref[:blocks]))
    ref[:block_graph_edge_map] = Dict{LightGraphs.Edge,Int}()
    ref[:block_switches] = Dict{Int,Set{Int}}(b => Set{Int}() for (b,_) in ref[:blocks])

    for (s,switch) in ref[:switch]
        f_block = ref[:bus_block_map][switch["f_bus"]]
        t_block = ref[:bus_block_map][switch["t_bus"]]
        LightGraphs.add_edge!(ref[:block_graph], f_block, t_block)
        ref[:block_graph_edge_map][LightGraphs.Edge(f_block, t_block)] = s
        ref[:block_graph_edge_map][LightGraphs.Edge(t_block, f_block)] = s

        if switch["dispatchable"] == 1 && switch["status"] == 1
            push!(ref[:block_switches][f_block], s)
            push!(ref[:block_switches][t_block], s)
        end
    end

    ref[:switch_scores] = Dict{Int,Real}(s => 0.0 for (s,_) in ref[:switch])
    for type in ["storage", "gen"]
        for (id,obj) in ref[Symbol(type)]
            if obj[PMD.pmd_math_component_status[type]] != PMD.pmd_math_component_status_inactive[type]
                start_block = ref[:bus_block_map][obj["$(type)_bus"]]
                paths = LightGraphs.enumerate_paths(LightGraphs.dijkstra_shortest_paths(ref[:block_graph], start_block))

                for path in paths
                    cumulative_weight = 0.0
                    for (i,b) in enumerate(reverse(path[2:end]))
                        cumulative_weight += ref[:block_weights][b]
                        b_prev = path[end-i]
                        ref[:switch_scores][ref[:block_graph_edge_map][LightGraphs.Edge(b_prev,b)]] += cumulative_weight
                    end
                end
            end
        end
    end
end


"""
    ref_add_load_blocks!(ref::Dict{Symbol,<:Any}, data::Dict{String,<:Any})

Ref extension to add load blocks to ref
"""
function ref_add_load_blocks!(ref::Dict{Symbol,<:Any}, data::Dict{String,<:Any})
    PMD.apply_pmd!(_ref_add_load_blocks!, ref, data; apply_to_subnetworks=true)
end


"Ref extension to add max_switch_actions to ref, and set to Inf if option is missing"
function _ref_add_max_switch_actions!(ref::Dict{Symbol,<:Any}, data::Dict{String,<:Any})
    ref[:max_switch_actions] = get(data, "max_switch_actions", Inf)
end


"""
    ref_add_max_switch_actions!(ref::Dict{Symbol,<:Any}, data::Dict{String,<:Any})

Ref extension to add max_switch_actions to ref, and set to Inf if option is missing
"""
function ref_add_max_switch_actions!(ref::Dict{Symbol,<:Any}, data::Dict{String,<:Any})
    PMD.apply_pmd!(_ref_add_max_switch_actions!, ref, data; apply_to_subnetworks=true)
end

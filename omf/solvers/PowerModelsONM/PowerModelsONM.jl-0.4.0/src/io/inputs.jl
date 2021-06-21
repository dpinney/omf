""
function prepare_network_case(network_file::String; events::Vector{<:Dict{String,Any}}=Vector{Dict{String,Any}}([]), time_elapsed::Real=1.0, vad::Real=3.0, vm_lb::Real=0.9, vm_ub::Real=1.1, clpu_factor::Real=2.0)::Tuple{Dict{String,Any},Dict{String,Any}}
    data_dss = PMD.parse_dss(network_file)

    # TODO: explicitly support DELTA connected generators in LPUBFDiag
    for type in ["pvsystem", "generator"]
        if haskey(data_dss, type)
            for (_,obj) in data_dss[type]
                obj["conn"] = PMD.WYE
            end
        end
    end

    data_eng = PMD.parse_opendss(data_dss; import_all=true)

    # Allow all loads to be sheddable
    for (_,load) in data_eng["load"]
        load["dispatchable"] = PMD.YES
        load["clpu_factor"] = clpu_factor
    end

    data_eng["voltage_source"]["source"]["pg_lb"] = zeros(length(data_eng["voltage_source"]["source"]["connections"]))
    data_eng["time_elapsed"] = time_elapsed  # 24 hours by default, 1 hr steps

    PMD.apply_voltage_bounds!(data_eng; vm_lb=vm_lb, vm_ub=vm_ub)
    apply_voltage_angle_bounds!(data_eng, vad)

    adjust_line_limits!(data_eng)

    # PMD.make_lossless!(data_eng)

    mn_data_eng = PMD._build_eng_multinetwork(data_eng)

    apply_events!(mn_data_eng, events)

    return data_eng, mn_data_eng
end


""
function parse_events(events_file::String)::Vector{Dict{String,Any}}
    open(events_file, "r") do f
        JSON.parse(f)
    end
end


""
function parse_inverters(inverter_file::String)::Dict{String,Any}
    PowerModelsStability.parse_json(inverter_file)
end


""
function parse_protection_tables(protection_file::String)::Dict{NamedTuple,Dict{String,Any}}
    _tables = Dict()

    XLSX.openxlsx(protection_file, mode="r") do xf
        for sheet_name in XLSX.sheetnames(xf)
            if sheet_name != "ConfigTable"
                _table = xf[sheet_name][:]
                _protection_types = Dict(idx => lowercase(strip(split(type,"-")[end])) for (idx,type) in enumerate(_table[1,:]) if !ismissing(type))
                type_idxs = sort([i for (i,_) in _protection_types])
                _col_headers = Dict(idx => lowercase(header) for (idx,header) in enumerate(_table[2,:]) if !ismissing(header))

                _data = _table[3:end,:]
                _tables[sheet_name] = Dict(type => Dict(header => [] for (jdx,header) in _col_headers) for (idx,type) in _protection_types)
                current_type = _protection_types[1]
                for (idx,header) in _col_headers
                    current_type = haskey(_protection_types,idx) ? _protection_types[idx] : current_type
                    for value in _data[:,idx]
                        push!(_tables[sheet_name][current_type][header], value)
                    end
                end
            else
                _tables[sheet_name] = DataFrames.DataFrame(XLSX.gettable(xf[sheet_name])...)
            end
        end
    end

    _configs = _tables["ConfigTable"]
    _config_num = _configs[!, Symbol("Config S#")]
    _switches = [n for n in names(_configs) if !startswith(n, "Config")]
    _namedtuple_names = Tuple(Symbol(replace(sw, "'" => "")) for sw in _switches)

    configurations = Dict{String,NamedTuple}()
    for (i, row) in enumerate(eachrow(_configs))
        configurations["S$(_config_num[i])"] = NamedTuple{_namedtuple_names}(Tuple(lowercase(string(PMD.SwitchState(row[sw]))) for sw in _switches))
    end

    protection_data = Dict{NamedTuple,Dict{String,Any}}()
    for (name, table) in _tables
        if name != "ConfigTable"
            protection_data[configurations[name]] = table
        end
    end

    return protection_data
end


""
function parse_faults(faults_file::String)::Dict{String,Any}
    JSON.parsefile(faults_file)
end

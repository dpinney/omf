"Custom type for comma separated list to Vector{String}"
function ArgParse.parse_item(::Type{Vector{String}}, x::AbstractString)
    return Vector{String}([string(strip(item)) for item in split(x, ",")])
end


"""
    parse_commandline(; validate::Bool=true)::Dict{String,Any}

Command line argument parsing

## Supported command line arguments

- `--network`, `-n`
- `--output`, `-o`
- `--faults`, `-f`
- `--events`, `-e`
- `--inverters`, `-i`
- `--settings`, `-s`
- `--quiet`, `-q`
- `--verbose`, `-v`
- `--debug`, `-d`
- `--gurobi`, `-g`
- `--opt-disp-formulation`
- `--opt-disp-solver`
- `--skip`

## Depreciated command line arguments

- `--network-file`
- `--output-file`
- `--problem`, `-p`
- `--formulation`
- `--protection-settings`
- `--debug-export-file`
- `--use-gurobi`
- `--solver-tolerance`
- `--max-switch-actions`
- `--timestep-hours`
- `--voltage-lower-bound`
- `--voltage-upper-bound`
- `--voltage-angle-difference`
- `--clpu-factor`

"""
function parse_commandline(; validate::Bool=true)::Dict{String,Any}
    s = ArgParse.ArgParseSettings(
        prog = "PowerModelsONM",
        description = "Optimization library for the operation and restoration of networked microgrids",
        autofix_names = false,
    )

    ArgParse.@add_arg_table! s begin
        "--network", "-n"
            help = "the power system network data file"
            arg_type = String
            # required = true
        "--output", "-o"
            help = "path to output file"
            default = ""
            arg_type = String
        "--faults", "-f"
            help = "json file defining faults over which to perform fault study"
            default = ""
            arg_type = String
        "--events", "-e"
            help = "Events (contingencies) file"
            default = ""
            arg_type = String
        "--inverters", "-i"
            help = "inverter settings file for stability analysis"
            default = ""
            arg_type = String
        "--settings", "-s"
            help = "general settings file for setting custom bounds and microgrid metadata"
            default = ""
            arg_type = String
        "--quiet", "-q"
            help = "sets log level in ONM to :Error"
            action = :store_true
        "--verbose", "-v"
            help = "info, warn messages for all packages"
            action = :store_true
        "--debug", "-d"
            help = "debug messages and output of full results for each optimization step"
            action = :store_true
        "--gurobi", "-g"
            help = "use the gurobi solver (must have been built with Gurobi.jl / a Gurobi binary, and have license)"
            action = :store_true
        "--opt-disp-formulation"
            help = "mathematical formulation to solve for the final optimal dispatch (lindistflow (default), acr, acp, nfa)"
            default = "lindistflow"
            arg_type = String
        "--opt-disp-solver"
            help = "optimization solver to use for the optimal dispatch problem (nlp_solver (default), misocp_solver, minlp_solver). Needs to match features in chosen opt-disp-formulation"
            default = "nlp_solver"
            arg_type = String
        "--skip"
            help = "comma separated list of parts of the algorithm to skip: faults, stability, dispatch, and/or switching"
            arg_type = Vector{String}
            default = String[]
        "--pretty-print"
            help = "flag to toggle pretty-printed output json"
            action = :store_true
    end

    # Depreciated Command Line Arguments
    ArgParse.@add_arg_table! s begin
        "--network-file"
            help = "DEPRECIATED: use 'network'"
            default = ""
            arg_type = String
        "--output-file"
            help = "DEPRECIATED: use 'output'"
            default = ""
            arg_type = String
        "--problem", "-p"
            help = "DEPRECIATED: ignored"
            default = "opf"
            arg_type = String
        "--formulation"
            help = "DEPRECIATED: use 'opt-disp-formulation'"
            default = ""
            arg_type = String
        "--protection-settings"
            help = "DEPRECIATED: ignored"
            default = ""
            arg_type = String
        "--debug-export-file"
            help = "DEPRECIATED: use 'debug'"
            default = ""
            arg_type = String
        "--use-gurobi"
            help = "DEPRECIATED: use 'gurobi'"
            action = :store_true
        "--solver-tolerance"
            help = "DEPRECIATED: use 'settings'"
            arg_type = Float64
        "--max-switch-actions"
            help = "DEPRECIATED: use 'settings'"
            arg_type = Int
        "--timestep-hours"
            help = "DEPRECIATED: use 'settings'"
            arg_type = Float64
        "--voltage-lower-bound"
            help = "DEPRECIATED: use 'settings'"
            arg_type = Float64
        "--voltage-upper-bound"
            help = "DEPRECIATED: use 'settings'"
            arg_type = Float64
        "--voltage-angle-difference"
            help = "DEPRECIATED: use 'settings'"
            arg_type = Float64
        "--clpu-factor"
            help = "DEPRECIATED: use 'settings'"
            arg_type = Float64
    end

    arguments = ArgParse.parse_args(s)

    for arg in collect(keys(arguments))
        if isnothing(arguments[arg]) || isempty(arguments[arg])
            delete!(arguments, arg)
        end
    end

    if validate && !validate_runtime_arguments(arguments)
        error("invalid runtime arguments detected")
    end

    _deepcopy_args!(arguments)

    return arguments
end


"""
    sanitize_args!(args::Dict{String,<:Any})::Dict{String,Any}

Sanitizes depreciated arguments into the correct new ones, and gives warnings

## Depreciated argument conversions

- `network-file` -> `network`
- `output-file` -> `output`
- `protection-settings` -> delete!
- `problem` -> delete!
- `formulation` -> `opt-disp-formulation`
- `debug-export-file` -> `debug=true`
- `use-gurobi` -> `gurobi`

"""
function sanitize_args!(args::Dict{String,<:Any})::Dict{String,Any}
    _deepcopy_args!(args)

    if !isempty(get(args, "network-file", ""))
        @warn "'network-file' argument is being depreciated in favor of 'network', please update your code"
        args["network"] = pop!(args, "network-file")
    end

    if !isempty(get(args, "output-file", ""))
        @warn "'output-file' argument is being depreciated in favor of 'output', please update your code"
        args["output"] = pop!(args, "output-file")
    end

    if !isempty(get(args, "protection-settings", ""))
        delete!(args, "protection-settings")
        @warn "'protection-settings' argument is depreciated, will be ignored"
    end

    if !isempty(get(args, "problem", ""))
        delete!(args, "problem")
        @warn "'problem' argument is depreciated, will be ignored"
    end

    if !isempty(get(args, "formulation", ""))
        args["opt-disp-formulation"] = pop!(args, "formulation")
        @warn "'formulation' argument is depreciated in favor of 'opt-disp-formulation', please update your code"
    end

    if haskey(args, "debug-export-file")
        if !isempty(get(args, "debug-export-file", ""))
            args["debug"] = true
        end
        @warn "'debug-export-file' argument is depreciated in favor of the 'debug' flag, file will be outputted to debug_{prob_type}_{current_time}.json, please update your code"
        delete!(args, "debug-export-file")
    end

    if get(args, "use-gurobi", false)
        args["gurobi"] = pop!(args, "use-gurobi")
        @warn "'use-gurobi' flag is depreciated in favor of 'gurobi' flag, please update your code"
    end

    for arg in ["solver-tolerance", "max-switch-actions", "timestep-hours", "voltage-lower-bound", "voltage-upper-bound", "voltage-angle-difference", "clpu-factor"]
        if haskey(args, arg)
            @warn "'$arg' argument is depreciated in favor of 'settings' input file, please update code"
        end
    end

    return args
end


"""
    _deepcopy_args!(args::Dict{String,<:Any})::Dict{String,Any}

Copies arguments to "raw_args" in-place in `args`, for use in [`entrypoint`](@ref entrypoint)
"""
function _deepcopy_args!(args::Dict{String,<:Any})::Dict{String,Any}
    if !haskey(args, "raw_args")
        args["raw_args"] = deepcopy(args)
    end
    return args["raw_args"]
end

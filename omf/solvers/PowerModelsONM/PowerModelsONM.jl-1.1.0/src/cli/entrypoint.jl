import ArgParse

include("arguments.jl")

args = parse_commandline(; validate=false)

# TODO: Remove use-gurobi when it gets removed from depreciated CLI Arguments
if get(args, "gurobi", false) || get(args, "use-gurobi", false)
    import Gurobi
end

import PowerModelsONM

if isinteractive() == false
    PowerModelsONM.entrypoint(args)
end

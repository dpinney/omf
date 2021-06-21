const _formulations = Dict{String,Any}(
    "acr" => PMD.ACRPowerModel,
    "acp" => PMD.ACPPowerModel,
    "lindistflow" => PMD.LPUBFDiagPowerModel,
    "nfa" => PMD.NFAPowerModel
)

const _mn_problems = Dict{String,Any}(
    "opf" => PMD.solve_mn_mc_opf,
    "mld" => PMD.solve_mn_mc_mld_simple
)

const _problems = Dict{String,Any}(
    "opf" => PMD.solve_mc_opf,
    "pf" => PMD.solve_mc_pf,
    "mld" => PMD.solve_mc_mld
)


""
function get_formulation(form_string::String)
    return _formulations[form_string]
end


""
function get_problem(problem_string::String, ismultinetwork)::Function
    return ismultinetwork ? _mn_problems[problem_string] : _problems[problem_string]
end

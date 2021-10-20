"string to PowerModelsDistribution type conversion for opt-disp-formulation"
const _formulations = Dict{String,Any}(
    "acr" => PMD.ACRUPowerModel,
    "acp" => PMD.ACPUPowerModel,
    "lindistflow" => PMD.LPUBFDiagPowerModel,
    "nfa" => PMD.NFAUPowerModel,
    "fot" => PMD.FOTRUPowerModel,
    "fbs" => PMD.FBSUBFPowerModel,
)

"helper function to convert from opt-disp-formulation string to PowerModelsDistribution Type"
_get_formulation(form_string::String) = _formulations[form_string]
_get_formulation(form::Type) = form

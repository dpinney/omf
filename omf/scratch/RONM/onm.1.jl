import Gurobi
using PowerModelsONM

PowerModelsONM.build_settings_file("nreca1824.dss", "settings.ieee8500.ts=60min.json"; max_switch_actions=1, vad_deg=5.0, vm_lb_pu=0.9, vm_ub_pu=1.1, line_limit_mult=Inf, sbase_default=1e3, time_elapsed=missing, mip_solver_gap=0.0001, mip_solver_tol=1e-6, nlp_solver_tol=1e-6)
PowerModelsONM.build_events_file("nreca1824.dss", "events.ieee8500.json"; default_switch_dispatchable=PMD.NO)

settings_files = [
    "settings.ieee8500.ts=60min.json",
]

args = Dict{String,Any}()

for switch_alg in ["global"]
    for settings_file in settings_files
        output_file = "output.$(join(split(settings_file, ".")[2:end-1], ".")).$(switch_alg).json"
        args = Dict{String,Any}(
            "network" => "nreca1824.dss",
            "verbose" => true,
            "gurobi" => true,
            "output" => "$(output_file)",
            "settings" => "$(settings_file)",
            "events" => "events.ieee8500.json",
            "opt-switch-algorithm" => switch_alg,
            "opt-disp-solver" => "misocp_solver",
            "fix-small-numbers" => true,
            "skip" => ["stability","faults"]
        )

        PowerModelsONM.entrypoint(args)
    end
end

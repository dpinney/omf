import Gurobi
using PowerModelsONM

import JSON

# build settings file
eng = PMD.parse_file("ieee8500-unbal_no_fuses.clean_reduced.good_coords.dss"; transformations=[PMD.apply_kron_reduction!])
n_steps = length(first(eng["time_series"]).second["values"])

# Init settings data structure with max_switch_actions set to 1, and 1 hr time steps
settings = Dict{String,Any}(
    "time_elapsed" => fill(1.0, n_steps),
    "max_switch_actions" => fill(1, n_steps),
    "bus" => Dict{String,Any}(),
    "line" => Dict{String,Any}(),
    "switch" => Dict{String,Any}(),
)

# Compute voltage bases for all buses
bus_vbases, line_vbases = PMD.calc_voltage_bases(eng, eng["settings"]["vbases_default"])

# Generate settings for buses
for (b, bus) in eng["bus"]
    settings["bus"][b] = Dict{String,Any}(
        "vm_lb" => fill(0.9 * bus_vbases[b], length(bus["terminals"])),  # Voltage magnitude lower bound
        "vm_ub" => fill(1.1 * bus_vbases[b], length(bus["terminals"])),  # Voltage magnitude upper bound
    )
end

# Generate settings for lines
for (l, line) in eng["line"]
    settings["line"][l] = Dict{String,Any}(
        "vad_lb" => fill(-5.0, length(line["f_connections"])), # voltage angle difference lower bound
        "vad_ub" => fill( 5.0, length(line["f_connections"])), # voltage angle different upper bound
    )
end

# Add switch defaults here
fixed_switches = String[]  # which switches are "fixed" (not dispatchable)
default_switch_states = Dict{String,PMD.SwitchState}() # what are the default switch states? PMD.OPEN or PMD.CLOSED

# Generate settings for switches
for (s, switch) in eng["switch"]
    settings["switch"][s] = Dict{String,Any}(
        "dispatchable" => Dict(true => PMD.YES, false => PMD.NO)[!(s in fixed_switches)],
        "state" => get(default_switch_states, s, PMD.CLOSED),
    )
end

# Save the settings.json file
open("settings.json", "w") do io
    JSON.print(io, settings, 2)
end

# run ONM
args = Dict{String,Any}(
    "network" => "ieee8500-unbal_no_fuses.clean_reduced.good_coords.dss",
    "verbose" => true,
    "gurobi" => true,
    "output" => "output.json",
    "settings" => "settings.json",
    "opt-switch-algorithm" => "global",
    "skip" => ["stability", "faults"]
)

out = entrypoint(args)

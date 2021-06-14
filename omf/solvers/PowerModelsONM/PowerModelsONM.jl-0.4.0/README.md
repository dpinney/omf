# PowerModelsONM

![CI](https://github.com/lanl-ansi/PowerModelsONM.jl/workflows/CI/badge.svg) ![Documentation](https://github.com/lanl-ansi/PowerModelsONM.jl/workflows/Documentation/badge.svg)

This package will combine various parts of the PowerModelsDistribution ecosystem to support the operation of networked microgrids.

Currently, only PowerModelsDistribution is being used in this prototype, so no actions are being performed other than generator dispatch (opf), and `"Device action timeline"` in the output specification will not be populated yet. Also, no additional inputs are needed yet other than a network case.

Also, note that Manifest.toml is currently needed in the repository because we are using a development branch of PowerModelsDistribution, but it will not be needed in the future.

## Running ONM

To run this code, use the latest release binaries to execute from the command line:

```bash
PowerModelsONM -n "path/to/Master.dss" -o "path/to/output.json"
```

This will execute with the following defaults:

- `"lindistflow"` formulation (LPUBFDiagPowerModel / LinDist3FlowPowerModel)
- `"opf"` problem (Optimal Power Flow)
- `1e-4` tolerance for Ipopt

### Options

- `-n` : path to network case (Master.dss)
- `-o` : path to output file (json)
- `-p` : problem type
  - optimal power flow ("opf": default, recommended),
  - maximal load delivery ("mld": will load shed, for debugging networks),
- `-f` : formulation
  - LinDistFlow approximation (`"lindistflow"`: default, recommended for speed, medium accuracy),
  - AC-rectangular (`"acr"`: slow, most accurate),
  - AC-polar (`"acp"`: slow, most accurate), or
  - network flow approximation (`"nfa"`: recommended for debugging, very fast, no voltages)
- `-v` : verbose output to command line
- `--solver-tolerance` : default `1e-4`, for debugging, shouldn't need to change
- `--debug-export-file` : exports the full results dict to the specified path
- `--events`: Contingencies / Events file (JSON) to apply to the network at runtime
- `--faults`: Pre-defined faults file (JSON) that contains faults over which to perform fault studies
- `--inverters`: Inverter settings file (JSON) that contains information for stability analysis
- `--protection-settings`: XLSX (Excel) file containing protection settings for various network configurations
- `--max-switch-actions`: maximum allowed switching actions per timestep
- `--timestep-duration`: duration of time between timesteps in hours

### Recommended networks

From PowerModelsRONMLib, use the following networks:

1. `iowa240/Master_hse_der_ts_03_05.dss`: 24h load shapes added to High Side Equivalent DER version for 03/05
1. `iowa240/Master_hse_der_ts_03_06.dss`: 24h load shapes added to High Side Equivalent DER version for 03/06
1. `iowa240/Master_hse_der_ts_03_15.dss`: 24h load shapes added to High Side Equivalent DER version for 03/15
<!-- 1. `iowa240/Master_hse_der_ts_03_05_c_1.dss`: 03/05 loadshapes with contingency on substation transformer -->
<!-- 1. `iowa240/Master_hse_der_ts_03_05_c_2.dss`: 03/05 loadshapes with contingency on feeder trunks -->

To apply contingencies, we need to use the Events format, e.g. `iowa240/outages/outage_1.json`, with the `--events` argument.

For example, using the compiled binary and all available files for iowa-240:

    PowerModelsONM -n "iowa240/Master_hsd_der_ts_03_05.dss" --events "iowa240/outages/outage_1.json --faults "iowa240/faults/faults.json" --protection-settings "iowa240/protection_settings/protection_settings.xlsx" --inverters "test/data/iowa240_inverters.json" -o "output.json"

## Output format

The current output format is the follow, which gets written to a json file:

```julia
Dict{String,Any}(
    "Simulation time steps" => Vector{String}(["$t" for t in timestamps]]),
    "Load served" => Dict{String,Vector{Real}}(
        "Feeder load (%)" => Vector{Real}([]),
        "Microgrid load (%)" => Vector{Real}([]),
        "Bonus load via microgrid (%)" => Vector{Real}([]),
    ),
    "Generator profiles" => Dict{String,Vector{Real}}(
        "Grid mix (kW)" => Vector{Real}([]),
        "Solar DG (kW)" => Vector{Real}([]),
        "Energy storage (kW)" => Vector{Real}([]),
        "Diesel DG (kW)" => Vector{Real}([]),
    ),
    "Voltages" => Dict{String,Vector{Real}}(
        "Min voltage (p.u.)" => Vector{Real}([]),
        "Mean voltage (p.u.)" => Vector{Real}([]),
        "Max voltage (p.u.)" => Vector{Real}([]),
    ),
    "Storage SOC (%)" => Vector{Real}([]),
    "Device action timeline" => Vector{Dict{String,Any}}([]),
    "Powerflow output" => Vector{Dict{String,Any}}([]),
    "Summary statistics" => Dict{String,Any}(),
    "Events" => Vector{Dict{String,Any}}([]),
    "Protection settings" => Vector{Dict{String,Any}}([]),
    "Small signal stable" => Vector{Bool}([]),
    "Device action timeline" => Vector{Dict{String,Any}}([]),
)
```

See API models in the `models` directory for details on the input and output formats.

## Running during Development

To run from within the Julia REPL,

```julia
args = Dict{String,Any}(
    "network-file" => "../iowa240/Master_hse_der_ts_03_05.dss",
    "output-file" => "output.json",
    "debug-export-file" => "",
    "formulation" => "lindistflow",
    "problem" => "opf",
    "solver-tolerance" => 1e-4,
    "events" => "../iowa240/outages/outage_1.json",
    "inverters" => "../test/data/iowa240_inverters.json",
    "protection-settings" => "../iowa240/protection_settings/protection_settings.xlsx",
    "faults" => "../iowa240/faults/faults.json",
)

using PowerModelsONM

entrypoint(args)
```

## Notes

## License

This code is provided under a BSD license as part of the Multi-Infrastructure Control and Optimization Toolkit (MICOT) project, LA-CC-13-108.

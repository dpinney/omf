@testset "test optimal dispatch" begin
    args = Dict{String,Any}(
        "network" => "../test/data/IEEE13Nodeckt_mod.dss",
        "settings" => "../test/data/settings.json",
    )

    parse_network!(args)
    parse_settings!(args)
    build_solver_instances!(args)

    args["opt-disp-formulation"] = "nfa"
    optimize_dispatch!(args)

    @test isapprox(args["optimal_dispatch_result"]["objective"], 10.3151; atol=1e-2)

    v_stats = get_timestep_voltage_statistics(args["optimal_dispatch_result"]["solution"], args["network"])
    @test all(all(isnan.(v)) for v in values(v_stats))

    disp_sol = get_timestep_dispatch(args["optimal_dispatch_result"]["solution"], args["network"])
    @test all(all(ismissing(switch["voltage (V)"]) for switch in values(timestep["switch"])) for timestep in disp_sol)

    args["opt-disp-formulation"] = "lindistflow"
    optimize_dispatch!(args)

    @test isapprox(args["optimal_dispatch_result"]["objective"], 10.2394; atol=1e-2)

    args["opt-disp-formulation"] = "acr"
    optimize_dispatch!(args)

    @test isapprox(args["optimal_dispatch_result"]["objective"], 10.4283; atol=1e-2)
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["700"]["vm"], [2.4560, 2.5484, 2.5329]; atol=1e-2))
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["700"]["va"], [-2.3790, -121.2439, 119.2539]; atol=1e-2))
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["671"]["vm"], [2.4279, 2.5864, 2.5226]; atol=1e-2))
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["671"]["va"], [-3.7399, -121.3441, 119.2225]; atol=1e-2))

    args["opt-disp-formulation"] = "acp"
    optimize_dispatch!(args)

    @test isapprox(args["optimal_dispatch_result"]["objective"], 10.4283; atol=1e-2)
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["700"]["vm"], [2.4560, 2.5484, 2.5329]; atol=1e-2))
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["700"]["va"], [-2.3790, -121.2439, 119.2539]; atol=1e-2))
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["671"]["vm"], [2.4279, 2.5864, 2.5226]; atol=1e-2))
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["671"]["va"], [-3.7399, -121.3441, 119.2225]; atol=1e-2))
end

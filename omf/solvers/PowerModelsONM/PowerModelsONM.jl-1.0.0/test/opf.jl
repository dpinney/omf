@testset "test optimal dispatch" begin
    args = Dict{String,Any}(
        "network" => "../test/data/IEEE13Nodeckt_mod.dss",
        "events" => "../test/data/events.json",
    )

    parse_network!(args)
    build_solver_instances!(args)

    args["opt-disp-formulation"] = "nfa"
    optimize_dispatch!(args)

    @test isapprox(args["optimal_dispatch_result"]["objective"], 6.893; atol=1e-2)

    args["opt-disp-formulation"] = "lindistflow"
    optimize_dispatch!(args)

    @test isapprox(args["optimal_dispatch_result"]["objective"], 6.554; atol=1e-2)

    args["opt-disp-formulation"] = "acr"
    optimize_dispatch!(args)

    @test isapprox(args["optimal_dispatch_result"]["objective"], 6.979; atol=1e-2)
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["700"]["vm"], [2.4676, 2.5471, 2.5706]; atol=1e-2))
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["700"]["va"], [-0.7483, -120.9461, 120.2302]; atol=1e-2))
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["671"]["vm"], [2.4394, 2.5846, 2.5612]; atol=1e-2))
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["671"]["va"], [-2.0905, -121.0381, 120.1962]; atol=1e-2))

    args["opt-disp-formulation"] = "acp"
    optimize_dispatch!(args)

    @test isapprox(args["optimal_dispatch_result"]["objective"], 6.979; atol=1e-2)
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["700"]["vm"], [2.4676, 2.5471, 2.5706]; atol=1e-2))
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["700"]["va"], [-0.7483, -120.9461, 120.2302]; atol=1e-2))
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["671"]["vm"], [2.4394, 2.5846, 2.5612]; atol=1e-2))
    @test all(isapprox.(args["optimal_dispatch_result"]["solution"]["nw"]["1"]["bus"]["671"]["va"], [-2.0905, -121.0381, 120.1962]; atol=1e-2))
end

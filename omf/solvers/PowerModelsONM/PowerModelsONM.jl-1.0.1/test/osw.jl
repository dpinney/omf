@testset "test optimal switching" begin
    args = Dict{String,Any}(
        "network" => "../test/data/IEEE13Nodeckt_mod.dss",
        "events" => "../test/data/events.json",
        "voltage-lower-bound" => 0.8,
        "voltage-upper-bound" => 1.2,
        "voltage-angle-difference" => 5.0,
        "max-switch-actions" => 1,
    )
    initialize_output!(args)
    parse_network!(args)
    parse_events!(args)
    parse_settings!(args)
    build_solver_instances!(args)

    optimize_switches!(args)

    @test isapprox(args["optimal_switching_results"]["1"]["objective"], 200; atol=2)
    @test isapprox(args["optimal_switching_results"]["2"]["objective"],   0.0015; atol=1e-4)
    @test isapprox(args["optimal_switching_results"]["3"]["objective"],   0.0016; atol=1e-4)

    actions = get_timestep_device_actions!(args)
    @test all(sl in ["700", "701"] for sl in actions[1]["Shedded loads"])
    @test actions[1]["Switch configurations"] == Dict{String,Any}("671700" => "open", "701702" => "open", "671692" => "closed")
    @test actions[2]["Switch configurations"] == Dict{String,Any}("671700" => "closed", "701702" => "open", "671692" => "closed")
    @test actions[3]["Switch configurations"] == Dict{String,Any}("671700" => "closed", "701702" => "closed", "671692" => "closed")
end

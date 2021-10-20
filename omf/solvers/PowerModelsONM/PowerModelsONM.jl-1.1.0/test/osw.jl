@testset "test optimal switching" begin
    @testset "test iterative optimal switching" begin
        args = Dict{String,Any}(
            "network" => "../test/data/IEEE13Nodeckt_mod.dss",
            "events" => "../test/data/events.json",
            "settings" => "../test/data/settings.json",
            "opt-switch-algorithm" => "iterative"
        )
        initialize_output!(args)
        parse_network!(args)
        parse_events!(args)
        parse_settings!(args)
        build_solver_instances!(args)

        optimize_switches!(args)

        @test isapprox(args["optimal_switching_results"]["1"]["objective"], 165.7451; atol=2)
        @test isapprox(args["optimal_switching_results"]["2"]["objective"],   1.5760; atol=1e-4)
        @test isapprox(args["optimal_switching_results"]["3"]["objective"],   0.8503; atol=1e-4)
        @test isapprox(args["optimal_switching_results"]["4"]["objective"],   0.4354; atol=1e-4)
        @test isapprox(args["optimal_switching_results"]["5"]["objective"],   0.0208; atol=1e-4)


        actions = get_timestep_device_actions!(args)
        @test all(sl in ["700", "701"] for sl in actions[1]["Shedded loads"])
        @test actions[1]["Switch configurations"] == Dict{String,Any}("671700" => "open", "701702" => "open", "671692" => "closed", "703800"=>"open", "800801"=>"open")
        @test actions[2]["Switch configurations"] == Dict{String,Any}("671692" => "closed", "671700" => "closed", "703800" => "open", "800801" => "open", "701702" => "open")
        @test actions[3]["Switch configurations"] == Dict{String,Any}("671692" => "closed", "671700" => "closed", "703800" => "open", "800801" => "open", "701702" => "closed")
        @test actions[4]["Switch configurations"] == Dict{String,Any}("671692" => "closed", "671700" => "closed", "703800" => "closed", "800801" => "open", "701702" => "closed")
        @test actions[5]["Switch configurations"] == Dict{String,Any}("671692" => "closed", "671700" => "closed", "703800" => "closed", "800801" => "closed", "701702" => "closed")
    end

    @testset "test global optimal switching" begin
        args = Dict{String,Any}(
            "network" => "../test/data/IEEE13Nodeckt_mod.dss",
            "events" => "../test/data/events.json",
            "settings" => "../test/data/settings.json",
            "opt-switch-algorithm" => "global"
        )
        initialize_output!(args)
        parse_network!(args)
        parse_events!(args)
        parse_settings!(args)
        build_solver_instances!(args)

        optimize_switches!(args)

        @test isapprox(args["optimal_switching_results"]["1"]["objective"], 168.628; atol=2)

        actions = get_timestep_device_actions!(args)
        @test all(sl in ["700", "701"] for sl in actions[1]["Shedded loads"])
        @test actions[1]["Switch configurations"] == Dict{String,Any}("671700" => "open", "701702" => "open", "671692" => "closed", "703800"=>"open", "800801"=>"open")
        @test actions[2]["Switch configurations"] == Dict{String,Any}("671692" => "closed", "671700" => "closed", "703800" => "open", "800801" => "open", "701702" => "open")
        @test actions[3]["Switch configurations"] == Dict{String,Any}("671692" => "closed", "671700" => "closed", "703800" => "open", "800801" => "open", "701702" => "closed")
        @test actions[4]["Switch configurations"] == Dict{String,Any}("671692" => "closed", "671700" => "closed", "703800" => "closed", "800801" => "open", "701702" => "closed")
        @test actions[5]["Switch configurations"] == Dict{String,Any}("671692" => "closed", "671700" => "closed", "703800" => "closed", "800801" => "closed", "701702" => "closed")
    end
end

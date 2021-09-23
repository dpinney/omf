@testset "test small signal stability analysis" begin
    args = Dict{String,Any}(
        "network" => "../test/data/IEEE13Nodeckt_mod.dss",
        "settings" => "../test/data/settings_no_strg.json",
        "inverters" => "../test/data/inverters.json",
    )

    parse_network!(args)
    parse_settings!(args)
    build_solver_instances!(args)

    run_stability_analysis!(args)

    # TODO once more complex stability features are available, needs better tests
    @test all(!r for r in values(args["stability_results"]))
end

@testset "test io functions" begin
    base_network, network  = parse_network("../test/data/IEEE13Nodeckt_mod.dss")

    @testset "test network parsing" begin
        @test PMD.ismultinetwork(network)
        @test !PMD.ismultinetwork(base_network)
        @test PMD.iseng(network) && PMD.iseng(base_network)

        @test length(network["nw"]) == 5

        @test network["nw"]["1"]["switch"]["671700"]["state"] == PMD.CLOSED
        @test network["nw"]["1"]["switch"]["671700"]["dispatchable"] == PMD.YES
        @test network["nw"]["1"]["switch"]["671700"]["status"] == PMD.ENABLED
    end

    @testset "test events parsing" begin
        raw_events = parse_events("../test/data/events.json")
        @test length(raw_events) == 7

        events = parse_events(raw_events, network)
        @test isa(events, Dict) && length(events) == 2
        @test events["1"]["switch"]["671700"]["dispatchable"] == PMD.NO
        @test events["1"]["switch"]["671700"]["state"] == PMD.OPEN
        @test events["1"]["switch"]["671700"]["status"] == PMD.ENABLED

        _network = apply_events(network, events)
        @test _network["nw"]["1"]["switch"]["671700"]["state"] == PMD.OPEN
        @test _network["nw"]["1"]["switch"]["671700"]["dispatchable"] == PMD.NO
        @test _network["nw"]["1"]["switch"]["671700"]["status"] == PMD.ENABLED

        @test _network["nw"]["2"]["switch"]["671700"]["dispatchable"] == PMD.YES

        @test _network["nw"]["3"]["switch"]["671700"]["dispatchable"] == PMD.YES
    end

    @testset "test settings parsing" begin
        settings = parse_settings("../test/data/settings.json")

        _network = apply_settings(network, settings)
        @test all(all(l["clpu_factor"] == 2.0 for l in values(nw["load"])) for nw in values(_network["nw"]))
        @test all(nw["max_switch_actions"] == 1 for nw in values(_network["nw"]))
        @test all(nw["time_elapsed"] == 0.1667 for nw in values(_network["nw"]))
    end

    @testset "test runtime args to settings conversion" begin
        args = Dict{String,Any}(
            "solver-tolerance" => 1e-4,
            "max-switch-actions" => 1,
            "timestep-hours" => 0.1667,
            "voltage-lower-bound" => 0.9,
            "voltage-upper-bound" => 1.1,
            "voltage-angle-difference" => 5.0,
            "clpu-factor" => 2.0,
        )
        orig_keys = collect(keys(args))

        args, settings = PowerModelsONM._convert_depreciated_runtime_args!(args, Dict{String,Any}(), base_network, length(network["nw"]))

        @test all(!haskey(args, k) for k in orig_keys)
        @test settings["nlp_solver_tol"] == 1e-4

        _network = apply_settings(network, settings)
        @test all(all(l["clpu_factor"] == 2.0 for l in values(nw["load"])) for nw in values(_network["nw"]))
        @test all(nw["max_switch_actions"] == 1 for nw in values(_network["nw"]))
        @test all(nw["time_elapsed"] == 0.1667 for nw in values(_network["nw"]))

        bus_vbase, line_vbase = PMD.calc_voltage_bases(base_network, base_network["settings"]["vbases_default"])
        @test all(all(isapprox.(bus["vm_lb"], 0.9 * bus_vbase[id])) for (id,bus) in settings["bus"])
        @test all(all(isapprox.(bus["vm_ub"], 1.1 * bus_vbase[id])) for (id,bus) in settings["bus"])

        @test all(all(line["vad_lb"] .== -5.0) && all(line["vad_ub"] .== 5.0) for (_,line) in settings["line"])
    end

    @testset "test inverters parsing" begin
        inverters = parse_inverters("../test/data/inverters.json")
    end

    @testset "test faults parsing" begin
        faults = parse_faults("../test/data/faults.json")

        @test all(fault["status"] == PMD.ENABLED for (bus,fts) in faults for (ft,fids) in fts for (fid,fault) in fids)
        @test all(isa(fault["g"], Matrix) && isa(fault["b"], Matrix) for (bus,fts) in faults for (ft,fids) in fts for (fid,fault) in fids)
        @test all(isa(fault["connections"], Vector{Int}) for (bus,fts) in faults for (ft,fids) in fts for (fid,fault) in fids)
    end
end

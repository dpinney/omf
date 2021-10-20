@testset "test statistical analysis functions" begin
    args = Dict{String,Any}(
        "network" => "../test/data/IEEE13Nodeckt_mod.dss",
        "events" => "../test/data/events.json",
        "settings" => "../test/data/settings.json",
        "inverters" => "../test/data/inverters.json",
        "faults" => "../test/data/faults.json",
        "quiet" => true
    )

    args = entrypoint(args)

    @testset "test output schema" begin
        @test validate_output(args["output_data"])
    end

    @testset "test action stats" begin
        args["output_data"]["Device action timeline"] == Dict{String,Any}[
            Dict("Shedded loads" => ["701", "700"], "Switch configurations" => Dict("671692" => "closed", "671700" => "open", "703800" => "open", "800801" => "open", "701702" => "open"))
            Dict("Shedded loads" => String[], "Switch configurations" => Dict("671692" => "closed", "671700" => "closed", "703800" => "open", "800801" => "open", "701702" => "open"))
            Dict("Shedded loads" => String[], "Switch configurations" => Dict("671692" => "closed", "671700" => "closed", "703800" => "open", "800801" => "open", "701702" => "closed"))
            Dict("Shedded loads" => String[], "Switch configurations" => Dict("671692" => "closed", "671700" => "closed", "703800" => "closed", "800801" => "open", "701702" => "closed"))
            Dict("Shedded loads" => String[], "Switch configurations" => Dict("671692" => "closed", "671700" => "closed", "703800" => "closed", "800801" => "closed", "701702" => "closed"))
        ]

        @test args["output_data"]["Switch changes"] == Vector{String}[String[], String["671700"], String["701702"], String["703800"], String["800801"]]

        @test all(isapprox.(metadata["mip_gap"], 0.0; atol=1e-4) for metadata in args["output_data"]["Optimal switching metadata"])
    end

    @testset "test dispatch stats" begin
        @test length(args["output_data"]["Powerflow output"]) == 5
        @test all(haskey(ts, "voltage_source") && haskey(ts, "solar") && haskey(ts, "bus") for ts in args["output_data"]["Powerflow output"])

        @test all(isapprox.(args["output_data"]["Powerflow output"][1]["voltage_source"]["source"]["real power setpoint (kW)"], [581.817, 468.862, 708.804]; atol=10))
        @test all(isapprox.(args["output_data"]["Powerflow output"][1]["voltage_source"]["source"]["reactive power setpoint (kVar)"], [244.1, 32.2534, 40.3543]; atol=10))

        @test all(isapprox.(args["output_data"]["Powerflow output"][1]["solar"]["pv1"]["real power setpoint (kW)"], [64.4937, 64.5079, 64.4985]; atol=5))
        @test all(isapprox.(args["output_data"]["Powerflow output"][1]["solar"]["pv1"]["reactive power setpoint (kVar)"], [41.2318, 41.2334, 41.2331]; atol=5))

        @test all(isapprox.(args["output_data"]["Powerflow output"][1]["switch"]["671692"]["real power flow (kW)"], [485.0,68.0,290.0]; atol=1e-1))
        @test all(isapprox.(args["output_data"]["Powerflow output"][1]["switch"]["671692"]["reactive power flow (kVar)"], [-17.606,-172.830,-6.770]; atol=1e-1))
        @test all(isapprox.(args["output_data"]["Powerflow output"][1]["switch"]["671692"]["voltage (V)"], args["output_data"]["Powerflow output"][1]["bus"]["671"]["voltage (V)"]))

        @test args["output_data"]["Optimal dispatch metadata"]["termination_status"] == "LOCALLY_SOLVED"
    end

    @testset "test fault stats" begin

    end

    @testset "test microgrid stats" begin
        @test all(isapprox.(args["output_data"]["Storage SOC (%)"], [79.16, 74.99, 70.8, 66.66, 61.1]; atol=1e-1))

        @test all(isapprox.(args["output_data"]["Load served"]["Bonus load via microgrid (%)"], 0.0))
        @test all(isapprox.(args["output_data"]["Load served"]["Feeder load (%)"], [83.87, 89.85, 95.17, 95.17, 94.76]; atol=1e-1))
        @test all(isapprox.(args["output_data"]["Load served"]["Microgrid load (%)"], [10.3, 10.3, 4.87, 4.87, 5.27]; atol=1e-1))

        @test all(isapprox.(args["output_data"]["Generator profiles"]["Diesel DG (kW)"], 0.0))
        @test all(isapprox.(args["output_data"]["Generator profiles"]["Energy storage (kW)"], [30.0, 30.0, 30.0, 30.0, 39.9]; atol=1e-1))
        @test all(isapprox.(args["output_data"]["Generator profiles"]["Solar DG (kW)"], [185.0, 185.0, 71.37, 71.37, 71.37]; atol=1e-1))
        @test all(isapprox.(args["output_data"]["Generator profiles"]["Grid mix (kW)"], [1745.3, 1869.9, 1980.5, 1980.5, 2000.4]; atol=1e-1))

    end

    @testset "test stability stats" begin
        @test all(!i for i in args["output_data"]["Small signal stable"])
    end
end

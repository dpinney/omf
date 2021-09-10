@testset "test statistical analysis functions" begin
    args = Dict{String,Any}(
        "network" => "../test/data/IEEE13Nodeckt_mod.dss",
        "events" => "../test/data/events.json",
        "settings" => "../test/data/settings.json",
        "inverters" => "../test/data/inverters.json",
        "faults" => "../test/data/faults.json",
        "voltage-lower-bound" => 0.8,
        "voltage-upper-bound" => 1.2,
        "voltage-angle-difference" => 5.0,
        "max-switch-actions" => 1,
        "quiet" => true
    )

    args = entrypoint(args)

    @testset "test output schema" begin
        @test validate_output(args["output_data"])
    end

    @testset "test action stats" begin
        args["output_data"]["Device action timeline"] == Dict{String,Any}[
            Dict{String,Any}(
                "Shedded loads" => String["700", "701"],
                "Switch configuration" => Dict{String,String}(
                    "671695" => "closed",
                    "671700" => "open",
                    "701702" => "open"
                )
            ),
            Dict{String,Any}(
                "Shedded loads" => String[],
                "Switch configuration" => Dict{String,String}(
                    "671695" => "closed",
                    "671700" => "closed",
                    "701702" => "open"
                )
            ),
            Dict{String,Any}(
                "Shedded loads" => String[],
                "Switch configuration" => Dict{String,String}(
                    "671695" => "closed",
                    "671700" => "closed",
                    "701702" => "closed"
                )
            )
        ]

        @test args["output_data"]["Switch changes"] == Vector{String}[String[], String["671700"], String["701702"]]
    end

    @testset "test dispatch stats" begin
        @test length(args["output_data"]["Powerflow output"]) == 3
        @test all(haskey(ts, "voltage_source") && haskey(ts, "solar") && haskey(ts, "bus") for ts in args["output_data"]["Powerflow output"])

        @test all(isapprox.(args["output_data"]["Powerflow output"][1]["voltage_source"]["source"]["real power setpoint (kW)"], [581.817, 468.862, 708.804]; atol=10))
        @test all(isapprox.(args["output_data"]["Powerflow output"][1]["voltage_source"]["source"]["reactive power setpoint (kVar)"], [244.1, 32.2534, 40.3543]; atol=10))

        @test all(isapprox.(args["output_data"]["Powerflow output"][1]["solar"]["pv1"]["real power setpoint (kW)"], [64.4937, 64.5079, 64.4985]; atol=5))
        @test all(isapprox.(args["output_data"]["Powerflow output"][1]["solar"]["pv1"]["reactive power setpoint (kVar)"], [41.2318, 41.2334, 41.2331]; atol=5))

        @test all(isapprox.(args["output_data"]["Powerflow output"][1]["switch"]["671692"]["real power flow (kW)"], [485.0,68.0,290.0]; atol=1e-1))
        @test all(isapprox.(args["output_data"]["Powerflow output"][1]["switch"]["671692"]["reactive power flow (kVar)"], [-17.606,-172.830,-6.770]; atol=1e-1))
        @test all(isapprox.(args["output_data"]["Powerflow output"][1]["switch"]["671692"]["voltage (V)"], args["output_data"]["Powerflow output"][1]["bus"]["671"]["voltage (V)"]))
    end

    @testset "test fault stats" begin

    end

    @testset "test microgrid stats" begin
        @test all(isnan.(args["output_data"]["Storage SOC (%)"]))

        @test all(isapprox.(args["output_data"]["Load served"]["Bonus load via microgrid (%)"], 0.0))
        @test all(isapprox.(args["output_data"]["Load served"]["Feeder load (%)"], [85.8, 91.2, 96.7]; atol=1e-1))
        @test all(isapprox.(args["output_data"]["Load served"]["Microgrid load (%)"], [9.4, 9.0, 3.2]; atol=1e-1))

        @test all(isapprox.(args["output_data"]["Generator profiles"]["Diesel DG (kW)"], 0.0))
        @test all(isapprox.(args["output_data"]["Generator profiles"]["Energy storage (kW)"], 0.0))
        @test all(isapprox.(args["output_data"]["Generator profiles"]["Solar DG (kW)"], [193.5, 185.0, 89.75]; atol=1e-1))
        @test all(isapprox.(args["output_data"]["Generator profiles"]["Grid mix (kW)"], [1759.5, 1869.9, 2699.5]; atol=1e-1))

    end

    @testset "test stability stats" begin
        @test all(!i for i in args["output_data"]["Small signal stable"])
    end
end

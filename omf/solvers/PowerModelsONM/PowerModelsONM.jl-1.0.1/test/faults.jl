@testset "test fault study algorithms" begin
    args = Dict{String,Any}(
        "network" => "../test/data/IEEE13Nodeckt_mod.dss",
        "faults" => "../test/data/faults.json",
    )

    parse_network!(args)
    build_solver_instances!(args)

    run_fault_studies!(args)

    @test all(isapprox.(args["fault_studies_results"]["1"]["701"]["3p"]["1"]["solution"]["fault"]["1"]["cf"], [6745.18, 6559.8, 5598.44]; atol=1e-1))
    @test all(isapprox.(args["fault_studies_results"]["1"]["701"]["ll"]["1"]["solution"]["fault"]["1"]["cf"], [5907.09, 5907.09]; atol=1e-1))
    @test all(isapprox.(args["fault_studies_results"]["1"]["701"]["lg"]["1"]["solution"]["fault"]["1"]["cf"], [3549.36]; atol=1e-1))

    @test all(isapprox.(args["fault_studies_results"]["1"]["701"]["3p"]["1"]["solution"]["switch"]["701702"]["cf_fr"], [32.3834, 32.3834, 32.3834]; atol=1e-1))
    @test all(isapprox.(args["fault_studies_results"]["1"]["701"]["ll"]["1"]["solution"]["switch"]["701702"]["cf_fr"], [6.49818, 6.49833, 6.49826]; atol=1e-1))
    @test all(isapprox.(args["fault_studies_results"]["1"]["701"]["lg"]["1"]["solution"]["switch"]["701702"]["cf_fr"], [3.89415, 3.89414, 3.89417]; atol=1e-1))

    analyze_results!(args)

    @test all(isapprox.(args["output_data"]["Fault currents"][1]["701_3p_1"]["switch"]["701702"]["|I| (A)"], [32.3834, 32.3834, 32.3834]; atol=1e-1))
end

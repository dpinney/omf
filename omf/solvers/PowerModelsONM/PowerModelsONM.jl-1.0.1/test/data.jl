@testset "data handling checks" begin
    base_network, network = parse_network("../test/data/IEEE13Nodeckt_mod.dss")
    events = parse_events("../test/data/events.json", network)
    network = apply_events(network, events)
    network["nw"]["1"]["switch"]["701702"]["state"] = PMD.OPEN

    math = PMD.transform_data_model(network)

    @test !all(values(identify_cold_loads(math["nw"]["1"])))

    @test PowerModelsONM._get_formulation(PMD.ACPUPowerModel) == PMD.ACPUPowerModel

    blocks = PMD.identify_blocks(math["nw"]["1"])

    @test !all(is_block_warm(math["nw"]["1"],block) for block in blocks)
end

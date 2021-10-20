@testset "test validate test data against schemas" begin
    events = JSON.parsefile("../test/data/events.json")
    @test validate_events(events)

    inverters = JSON.parsefile("../test/data/inverters.json")
    @test validate_inverters(inverters)

    settings = JSON.parsefile("../test/data/settings.json")
    @test validate_settings(settings)

    faults = JSON.parsefile("../test/data/faults.json")
    @test validate_faults(faults)

    args = JSON.parsefile("../test/data/runtime_args_example.json")
    @test validate_runtime_arguments(args)
end

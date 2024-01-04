using JSON

include("REoptSolver/src/REoptSolver.jl") #joinpath(@__DIR__,

function test()
	json_data = JSON.parsefile(joinpath(@__DIR__, "julia_default.json"))
	json_data["ElectricLoad"]["path_to_csv"] = joinpath(@__DIR__,"testFiles/loadShape.csv")

    open(joinpath(@__DIR__, "testFiles/Scenario_test_POST.json"), "w") do file 
        JSON.print(file, json_data)
    end
	REoptSolver.run(joinpath(@__DIR__,"testFiles"), true)
end

test()
using PowerModelsONM

import Ipopt

ipopt_solver = PowerModelsONM.PMD.optimizer_with_attributes(Ipopt.Optimizer, "tol"=>1e-6, "print_level"=>0)

using Test

@testset "PowerModelsONM" begin
    # TODO: add unit tests
end

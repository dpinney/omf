module REoptSolver

export run

using REopt, JuMP, JSON, HiGHS #SCIP #, Cbc
#Ipopt, ECOS, Clp, GLPK


function get_model(solver::String, max_runtime_s::Union{Nothing,Int})
	if solver == "SCIP"
		m = Model(SCIP.Optimizer)
		#testing SCIP attributes
		#set_attribute(m, "display/verblevel", 0) # default is 4 - only change once done testing
		#set_attribute(m, "limits/gap", 0.08) #default is 0
		#set_attribute(m, "limits/solutions", 20) #default is infinity
		#set_attribute(m, "lp/threads", 8) #default = 0, max = 64
		#set_attribute(m, "parallel/minnthreads", 8) # default = 1, max = 64 
		if max_runtime_s != nothing
			set_attribute(m, "limits/time", max_runtime_s)
		end
		return m
	elseif solver == "HiGHS"
		m = Model(HiGHS.Optimizer)
		set_attribute(m,"threads",4)
        if max_runtime_s != nothing
            set_attribute(m,"time_limit", float(max_runtime_s))
        end
		return m
	else 
		println("Error: invalid solver")
	end
end


function results_to_json(results, output_path)
	j = JSON.json(results)

	open(output_path, "w") do file
		println(file, j)
	end
end


#currently available solvers: SCIP, HiGHS
function run(json_path::String, reopt_inputs_path::String, output_path::String, outage_path::Union{Nothing,String}=nothing, 
    solver::String="SCIP", microgrid_only::Bool=false, max_runtime_s::Union{Nothing,Int}=nothing)

	m = get_model(solver, max_runtime_s)
	m2 = get_model(solver, max_runtime_s)

	#writing REoptInputs to JSON for easier access of default values in microgridDesign
	reopt_inputs = REoptInputs(json_path)
	results_to_json(reopt_inputs,reopt_inputs_path)

	results = run_reopt([m,m2],json_path)

	results_to_json(results, output_path)

	if outage_path != nothing
		outage_results = simulate_outages(results, reopt_inputs; microgrid_only=microgrid_only)

		results_to_json(outage_results,outage_path)
	end

end

end 

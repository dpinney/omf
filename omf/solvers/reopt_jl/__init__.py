import json, time
import os, platform

#html output visuals
#import test_outputs
#from omf.solvers.reopt_jl import test_outputs

thisDir = os.path.abspath(os.path.dirname(__file__))

#not currently working : REopt dependency (ArchGDAL) unable to precompile
#def build_julia_image():
#    os.system(f'''julia --project={thisDir}/REoptSolver -e '
#            import Pkg; Pkg.add("PackageCompiler");
#            using PackageCompiler; include("{thisDir}/REoptSolver/src/REoptSolver.jl");
#            PackageCompiler.precompile("REoptSolver")
#            ' ''')


#potential add: boolean to determine if you want to check your install
# => improve runtime if running multiple times in a row
def install_reopt_jl(system : list = platform.system()):
    if os.path.isfile(f'{thisDir}/instantiated.txt'):
        print("REopt.jl dependencies installed - to reinstall remove file: instantiated.txt")
        return
    
    if system == "Darwin":
        commands = [
            'HOMEBREW_NO_AUTO_UPDATE=1 brew list julia 1>/dev/null 2>/dev/null || brew install julia@1.9.3'
        ]
    elif system == "Linux":
        commands = [
            'rm "julia-1.9.3-linux-x86_64.tar.gz"',
			'wget "https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.3-linux-x86_64.tar.gz"',
			'tar -x -f "julia-1.9.3-linux-x86_64.tar.gz" -C /usr/local --strip-components 1'
        ]
    else:
        print(f'No installation script available yet for {system}')
        return
    
    commands += [
            '''pip3 show julia 1>/dev/null 2>/dev/null || 
            { pip3 install julia; python3 -c 'import julia; julia.install()'; }''',
            f'touch {thisDir}/instantiated.txt'
            ]
    
    for command in commands:
        os.system(command)
    #build_julia_image()

########################################################
#functions for converting REopt input to REopt.jl input
########################################################

#dictionary mapping REopt variable name to REopt.jl variable name 
#  plus necessary information on parent section & data type
    # ( translated variable name , section(s)(/none) , datatype(None if multiple types) )
def init_reopt_to_julia_dict():
    to_jl_dict = { "Site":("Site", {None}, dict),
              "latitude":("latitude",{"Site"},float),
              "longitude":("longitude",{"Site"},float),

              "ElectricTariff":("ElectricTariff", {None}, dict), 
              "wholesale_rate_us_dollars_per_kwh":("wholesale_rate", {"ElectricTariff"}, None),
              "blended_annual_rates_us_dollars_per_kwh":
              ("blended_annual_energy_rate", {"ElectricTariff"}, None),
              "blended_annual_demand_charges_us_dollars_per_kw":
              ("blended_annual_demand_rate", {"ElectricTariff"}, None),
              "urdb_label":("urdb_label",{"ElectricTariff"},str),

              "LoadProfile":("ElectricLoad", {None}, dict),
              "critical_loads_kw":("critical_loads_kw",{"ElectricLoad"},list),
              "critical_load_pct":("critical_load_fraction",{"ElectricLoad"}, float),
              "loads_kw":("loads_kw",{"ElectricLoad"},list), "year":("year",{"ElectricLoad"},int), 
              "loads_kw_is_net":("loads_kw_is_net",{"ElectricLoad"},bool),

              "Financial":("Financial", {None}, dict),
              "value_of_lost_load_us_dollars_per_kwh":("value_of_lost_load_per_kwh", {"Financial"}, float), 
              "om_cost_escalation_pct":("om_cost_escalation_rate_fraction", {"Financial"}, float),
              "offtaker_discount_pct":("offtaker_discount_rate_fraction",{"Financial"}, float),
              "analysis_years":("analysis_years",{"Financial"}, int),

              #PV, ElectricStorage, Wind & Generator shared variables:
              "installed_cost_us_dollars_per_kw":
              ("installed_cost_per_kw", {"PV","Wind","ElectricStorage","Generator"} ,float),
              "min_kw":("min_kw", {"PV","Wind","ElectricStorage","Generator"}, float),
              "max_kw":("max_kw", {"PV","Wind","ElectricStorage","Generator"}, float), 
              "macrs_option_years":("macrs_option_years", {"PV","Wind","ElectricStorage","Generator"}, int),

              #PV, Wind, Generator shared:
              "can_export_beyond_site_load":("can_export_beyond_nem_limit", {"PV","Wind","Generator"}, bool),
              "federal_itc_pct":("federal_itc_fraction", {"PV","Wind","Generator"}, float),

              #Generator & ElectricStorage shared:
              "replace_cost_us_dollars_per_kw":("replace_cost_per_kw",{"Generator","ElectricStorage"},float),

              #PV & Generator shared:
              "can_curtail":("can_curtail", {"PV", "Generator"}, bool), 
              "existing_kw":("existing_kw", {"PV", "Generator"}, float), 
              "om_cost_us_dollars_per_kw":("om_cost_per_kw", {"PV", "Generator"}, float),

              "PV":("PV", {None}, dict),

              "Storage":("ElectricStorage", {None}, dict),
              "replace_cost_us_dollars_per_kwh":("replace_cost_per_kwh", {"ElectricStorage"}, float),
              "total_itc_percent":("total_itc_fraction", {"ElectricStorage"}, float),
              "inverter_replacement_year":("inverter_replacement_year", {"ElectricStorage"}, int),
              "battery_replacement_year":("battery_replacement_year", {"ElectricStorage"}, int), 
              "min_kwh":("min_kwh", {"ElectricStorage"}, float), 
              "max_kwh":("max_kwh", {"ElectricStorage"}, float),
              "installed_cost_us_dollars_per_kwh":("installed_cost_per_kwh", {"ElectricStorage"}, float),

              "Wind":("Wind", {None}, dict),

              "Generator":("Generator", {None}, dict),
              "generator_only_runs_during_grid_outage":("only_runs_during_grid_outage",{"Generator"}, bool),
              "fuel_avail_gal":("fuel_avail_gal", {"Generator"}, float), 
              "min_turn_down_pct":("min_turn_down_fraction", {"Generator"}, float),
              "diesel_fuel_cost_us_dollars_per_gallon":("fuel_cost_per_gallon", {"Generator"}, float),
              "emissions_factor_lb_CO2_per_gal":("emissions_factor_lb_CO2_per_gal", {"Generator"}, float),
              "om_cost_us_dollars_per_kwh":("om_cost_per_kwh", {"Generator"}, float),

              #### ElectricUtility (not used in REopt)
              "outage_start_time_step":("outage_start_time_step", {"ElectricUtility"}, int), 
              "outage_end_time_step":("outage_end_time_step", {"ElectricUtility"}, int)
    }

    #variables in reopt that aren't used in reopt.jl
    not_included_in_jl = { "outage_is_major_event", "wholesale_rate_above_site_load_us_dollars_per_kwh" }

    return (to_jl_dict, not_included_in_jl)


class KeyNotRecognizedError(Exception):
    def __init__(self, key):
        super().__init__(f"Key not found in API -> Julia JSON translator: {key}")
        self.key = key

class SectionLookupError(Exception):
    def __init__(self, key):
        super().__init__(f"No sections found for key: {key} in API -> Julia JSON translator")
        self.key = key

#checks if variable name is used in REopt.jl
def check_key(key, to_jl_dict, not_included_in_jl):
    if key in not_included_in_jl:
        return False
    elif key not in to_jl_dict:
        raise(KeyNotRecognizedError)
    else:
        return True
    
#returns data value if it is the correct data type or converts if feasible 
def check_input(key,var,to_jl_dict):
    if key in to_jl_dict:
        var_type = to_jl_dict[key][2]
        if var_type == type(var) or var_type == None:
            return var
        elif var_type == int:
            return int(var)
        elif var_type == float:
            return float(var)
    else:
        raise(KeyNotRecognizedError)

#returns converted section name if used in REopt.jl
def get_section(key,section,to_jl_dict):
    section_to_jl = to_jl_dict[section][0]
    new_sections = to_jl_dict[key][1]
    if section_to_jl in new_sections:
        return section_to_jl
    elif len(new_sections) == 1:
        return list(new_sections)[0]
    else:
        raise(SectionLookupError)

#converts variable into REopt.jl version of variable and adds to json
def add_variable(section,key,value,jl_json,to_jl_dict):
    new_section = get_section(key,section,to_jl_dict)
    new_var_name = to_jl_dict[key][0]
    if not new_section in jl_json:
        jl_json[new_section] = dict()
    jl_json[new_section][new_var_name] = check_input(key,value,to_jl_dict)
    return jl_json


#converts an input json for REopt to the equivalent version for REopt.jl

#REopt json: {Scenario: { Site: {lat, lon, ElectricTariff:{}, LoadProfile:{}, etc. }}}
#REopt.jl json: { Site: { lat, lon }, ElectricTariff:{}, LoadProfile:{}, etc. }
def convert_to_jl(reopt_json):
    (to_jl_dict,not_included_in_jl) = init_reopt_to_julia_dict()
    new_jl_json = {}
    try:
        scenario = reopt_json["Scenario"]["Site"]
        for key in scenario:
            if not check_key(key,to_jl_dict,not_included_in_jl):
                continue 
            value = scenario[key]
            if not type(value) == dict:
                new_jl_json = add_variable("Site",key,value,new_jl_json,to_jl_dict)
            else:
                for sub_key in value:
                    if not check_key(sub_key,to_jl_dict,not_included_in_jl): 
                            continue
                    else:
                        new_jl_json = add_variable(key,sub_key,value[sub_key],new_jl_json,to_jl_dict)
    except Exception as e:
        print(e)
    return new_jl_json

# for accessing & setting names of input/output json files

def get_json(inputPath):
    with open(inputPath) as j:
        inputJson = json.load(j)
    return inputJson

def write_json(outputPath, jsonData):
    if os.path.exists(outputPath):
        print(f'File {outputPath} already exists: overwriting')
    with open(outputPath, "w") as j:
        json.dump(jsonData, j)

#input and output file names used with reopt_jl solver
def get_file_names(path, inputFile, default, convert, outages, solver, solver_in_filename):
    inFile = inputFile if not default else "julia_default.json"
    #input path to file chosen by user : default file found in current directory
    inputPath = f'{path}/{inFile}' if not default else f'{thisDir}/{inFile}'
    #path given to julia solver
    jlInPath = f'{path}/converted_{inputFile}' if convert and not default else inputPath

    REoptInputsPath = f'{path}/REoptInputs.json'

    outFile = f'{solver}_{inFile}' if solver_in_filename else inFile
    #path for output file
    outputPath = f'{path}/out_{outFile}'
    #path for output outage file if simulating outages
    outagePath = f'{path}/outages_{outFile}' if outages else None 

    return (inputPath, jlInPath, REoptInputsPath, outputPath, outagePath)

##########################################################################
# run_reopt_jl : calls 'run' function through run_reopt.jl (Julia file)
##########################################################################

#todo: add options to set output path (and outage output path) ?
#potential optional inputs (for solver): ratio_gap, threads, max_solutions, verbosity
def run_reopt_jl(path, inputFile="", default=False, convert=True, outages=False, microgrid_only=False,
                 solver="HiGHS", solver_in_filename=True, max_runtime_s=None):
    
    if inputFile == "" and not default:
        print("Invalid inputs: inputFile needed if default=False")
        return

    install_reopt_jl()

    file_info = (path, inputFile, default, convert, outages, solver, solver_in_filename)
    (inPath, jlInPath, REoptInputsPath, outPath, outagePath) = get_file_names( *file_info )

    try:
        if convert and not default: #default file is already converted
            input_json = get_json(inPath)
            reopt_jl_input_json = convert_to_jl(input_json)
            write_json(jlInPath, reopt_jl_input_json)

        from julia import Pkg #Julia, Main
        #Julia(runtime=f'{thisDir}/reopt_jl.so') 
        #from julia import REoptSolver
        Pkg.activate(f'{thisDir}/REoptSolver')
        from julia import REoptSolver

        REoptSolver.run(jlInPath, REoptInputsPath, outPath, outagePath, solver, microgrid_only, max_runtime_s)
        #Main.include(f'{thisDir}/REoptSolver/src/REoptSolver.jl')
        #Main.run(jlInPath, outPath, outagePath, solver, microgrid_only, max_runtime_s)
        #todo: return output & outage path(s)? (decide on usage within models)
    except Exception as e:
        print(e)

###########################################################################
# comparing REopt.jl outputs for different test cases / solvers
###########################################################################

def runAllSolvers(path, testName, fileName="", default=False, convert=True, outages=True, 
                  solvers=["SCIP","HiGHS"], solver_in_filename=True, max_runtime_s=None,
                  get_cached=True ):
    test_results = []

    for solver in solvers:
        print(f'########## Running {solver} test: {testName}')
        start = time.time()

        file_info = (path, fileName, default, convert, outages, solver, solver_in_filename)
        (_, _, outPath, outagePath) = get_file_names( *file_info )

        if get_cached and os.path.isfile(outPath):
            print("this test was already run: loading cached results")
        else:
            run_reopt_jl(path, inputFile=fileName, default=default, solver=solver, outages=outages,
                         max_runtime_s=max_runtime_s)

        end = time.time()
        runtime = end - start
        test_results.append((outPath, outagePath, testName, runtime, solver, outages, get_cached))
        print(f'########## Completed {solver} test: {testName}')
 
    return(test_results)


def _test():
    all_tests = []
    all_solvers = [ "HiGHS" ] # "Ipopt", "ECOS", "Clp", "GLPK", "SCIP", "Cbc"
    path = f'{thisDir}/testFiles'

    ########### CONWAY_MG_MAX: 
    # CONWAY_MG.json copied from CONWAY_MG_MAX/Scenario_test_POST.json
    CONWAY_tests = runAllSolvers(path, "CONWAY_MG_MAX", fileName="CONWAY_MG.json", solvers=all_solvers,
                                 get_cached=False)
    all_tests.extend(CONWAY_tests)
    
    ############### CE test case
    # CE.json copied from CE Test Case/Scenario_test_POST.json
    CE_tests = runAllSolvers(path, "CE Test Case", fileName="CE.json", solvers=all_solvers,
                             get_cached=False, max_runtime_s=240)
    all_tests.extend(CE_tests)

    ############## CONWAY_30MAY23_SOLARBATTERY
    # CONWAY_SB.json copied from CONWAY_30MAY23_SOLARBATTERY/Scenario_test_POST.json
    CONWAY_SB_tests = runAllSolvers(path, "CONWAY_30MAY23_SOLARBATTERY", fileName="CONWAY_SB.json",
                                   solvers=all_solvers, get_cached=False)
    all_tests.extend(CONWAY_SB_tests)

    ####### default julia json (default values from microgridDesign)
    default_tests = runAllSolvers(path, "Julia Default", default=True, solvers=all_solvers, 
                                  get_cached=False)
    all_tests.extend(default_tests)

    #test_outputs.html_comparison(all_tests) # => test_outputs.py (work in progress)

if __name__ == "__main__":
    _test()
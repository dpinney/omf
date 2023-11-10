import json, time
import os, platform

thisDir = os.path.abspath(os.path.dirname(__file__))

def build_julia_image():
    os.system(f'''julia --project={thisDir}/REoptSolver -e '
            import Pkg; import REoptSolver; using PackageCompiler; 
            PackageCompiler.create_sysimage(["REoptSolver"]; sysimage_path="{thisDir}/reopt_jl.so")
            ' ''')

#potential add: boolean to determine if you want to check your install
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
    build_julia_image()

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

# for reading and writing input/output json files
def get_json(inputPath):
    with open(inputPath) as j:
        inputJson = json.load(j)
    return inputJson

def write_json(outputPath, jsonData):
    if os.path.exists(outputPath):
        print(f'File {outputPath} already exists: overwriting')
    with open(outputPath, "w") as j:
        json.dump(jsonData, j)

##########################################################################
# run_reopt_jl : calls 'run' function through run_reopt.jl (Julia file)
##########################################################################

#potential optional inputs (for solver): ratio_gap, threads, max_solutions, verbosity
def run_reopt_jl(path, inputFile="", default=False, convert=False, outages=False, microgrid_only=False,
                 solver="HiGHS", max_runtime_s=None):
    
    if inputFile == "" and not default:
        print("Invalid inputs: inputFile needed if default=False")
        return

    install_reopt_jl()

    constant_file = "Scenario_test_POST.json"
    constant_path = f'{path}/{constant_file}'

    if inputFile != constant_file:
        inputPath = f'{path}/{inputFile}'
        if default == True:
            inputPath = f'{thisDir}/julia_default.json'
        input_json = get_json(inputPath)
        write_json(constant_path, input_json)

    try:
        if convert and not default: #default file is already converted
            input_json = get_json(constant_path)
            reopt_jl_input_json = convert_to_jl(input_json)
            write_json(constant_path, reopt_jl_input_json)

        microgrid_only_conv = "false" if not microgrid_only else "true"
        outages_conv = "false" if not outages else "true"
        max_runtime_s_conv = "nothing" if max_runtime_s == None else max_runtime_s

        os.system(f'''julia --sysimage={f'{thisDir}/reopt_jl.so'} -e '
                  using .REoptSolver; 
                  REoptSolver.run("{path}", {outages_conv}, "{solver}", {microgrid_only_conv}, {max_runtime_s_conv})
                  ' ''')
    except Exception as e:
        print(e)

###########################################################################
# comparing REopt.jl outputs for different test cases / solvers
###########################################################################

def runAllSolvers(path, testName, fileName="", default=False, convert=True, outages=True, solvers=["SCIP","HiGHS"], max_runtime_s=None):

    for solver in solvers:
        print(f'########## Running {solver} test: {testName}')
        start = time.time()

        run_reopt_jl(path, inputFile=fileName, default=default, convert=convert, solver=solver, outages=outages, max_runtime_s=max_runtime_s)

        end = time.time()
        runtime = end - start
        print(f'########## Completed {solver} test: {testName} in {runtime} seconds')


def _test():
    all_solvers = [ "HiGHS" ] # "Ipopt", "ECOS", "Clp", "GLPK", "SCIP", "Cbc"
    path = f'{thisDir}/testFiles'

    ########### CONWAY_MG_MAX: 
    # CONWAY_MG.json copied from CONWAY_MG_MAX/Scenario_test_POST.json
    #runAllSolvers(path, "CONWAY_MG_MAX", fileName="CONWAY_MG.json", solvers=all_solvers)
    
    ############### CE test case
    # CE.json copied from CE Test Case/Scenario_test_POST.json
    #runAllSolvers(path, "CE Test Case", fileName="CE.json", solvers=all_solvers, max_runtime_s=240)

    ############## CONWAY_30MAY23_SOLARBATTERY
    # CONWAY_SB.json copied from CONWAY_30MAY23_SOLARBATTERY/Scenario_test_POST.json
    #runAllSolvers(path, "CONWAY_30MAY23_SOLARBATTERY", fileName="CONWAY_SB.json", solvers=all_solvers)

    ####### default julia json (default values from microgridDesign)
    #runAllSolvers(path, "Julia Default", default=True, solvers=all_solvers)

if __name__ == "__main__":
    _test()
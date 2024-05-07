import os, time, json, platform
import pandas, openpyxl
import requests as req
import keyring

urlBase = 'https://microgrids1.lbl.gov:4000/api/xls' 
fileMimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

lock_file = "lock_file.txt"

thisDir = os.path.abspath(os.path.dirname(__file__))

def get_credentials():
    '''returns API key for current user from keyring'''
    userKey = keyring.get_password("my_program", "user")
    return userKey

def set_credentials():
    '''sets current user's API key using keyring'''
    userKey = input("Enter your API key for the DER-CAM API ( sign up found here: https://dercam-app.lbl.gov/u/api ): ")
    keyring.set_password("my_program", "user", userKey)
    return userKey

def testfile_path(fileName):
    ''' returns file path to the given file within testFiles folder '''
    return os.path.normpath(os.path.join(thisDir,"testFiles",fileName))

def check_for_existing_file( der_cam_file ):
    ''' removes previous der_cam input file '''
    if os.path.exists( der_cam_file ):
        os.remove( der_cam_file )

def build_input_spreadsheet(path, reopt_input_file, der_cam_file_name ):
    ### work in progress
    '''builds file input for der-cam api given REopt input json'''

    reopt_file_path = os.path.normpath(os.path.join(path,reopt_input_file))
    der_cam_file_path = os.path.normpath(os.path.join(path,der_cam_file_name))

    #load reopt input file (reopt_input_file -> input_json)
    with open(reopt_file_path) as j:
        input_json = json.load(j)

    #load default der-cam excel input (test.xlsx)
    base_file = testfile_path("test.xlsx")
    xls = pandas.ExcelFile(base_file)
    sheets = xls.sheet_names

    check_for_existing_file(der_cam_file_path)
    create_new_file = True

    financial = input_json.get("Financial",None)
    pv = input_json.get("PV",None)
    wind = input_json.get("Wind",None)
    es = input_json.get("ElectricStorage",None)
    generator = input_json.get("Generator",None)

    def set_invest(df, tech, min, existing, max):
        #for min_kw <= max_kw & existing_kw <= max_kw (todo: input checking for user interface portion)
        if existing > 0:
            df.at[tech,"FixedInvest"] = 0
            df.at[tech,"ForcedInvestCapacity"] = existing
            df.at[tech,"ExistingYN"] = 1
        elif min > 0:
            df.at[tech, "FixedInvest"] = 0
            df.at[tech,"ForcedInvestCapacity"] = min
        elif max > 0:
            df.at[tech,"FixedInvest"] = 0
        return df

    #save each sheet (some with replacements) to new der-cam excel input file (der_cam_file_name)
    for sheet in sheets:
        hasIndex = True
        hasHeader = False
        if sheet == "FinancialSettings":
            df = pandas.read_excel(base_file, sheet_name=sheet, header=None, index_col=0)
            df.at["DiscRate",df.columns[0]] = financial.get("offtaker_discount_rate_fraction")
            df.at["MaxPaybackPeriod",df.columns[0]] = financial.get("analysis_years")

        if sheet == "GeneralReliabilityParams":
            df = pandas.read_excel(base_file, sheet_name=sheet, header=None, index_col=0)
            df.at["VOLL",df.columns[0]] = financial.get("value_of_lost_load_per_kwh")

        if sheet == "SolarCostParameters" and pv != None:
            df = pandas.read_excel(base_file, sheet_name=sheet, header=None, index_col=0)
            df.at["PV","VariableCost"] = pv.get("installed_cost_per_kw")
            df.at["PV","Lifetime"] = pv.get("macrs_option_years")

        if sheet == "SolarInvestParameters" and pv != None:
            df = pandas.read_excel(base_file, sheet_name=sheet, index_col=0)
            #hasHeader = True
            df = set_invest(df, "PV", pv.get("min_kw"), pv.get("existing_kw"), pv.get("max_kw"))

        if sheet == "PowerExportOptions" and pv != None:
            df = pandas.read_excel(base_file, sheet_name=sheet, header=None, index_col=0)
            can_export = int(pv.get("can_export_beyond_nem_limit"))
            df.at["NetMetering",df.columns[0]] = can_export 
            df.at["RenewableExport",df.columns[0]] = can_export

        if sheet == "GeneralTechConstrains" and pv != None:
            df = pandas.read_excel(base_file, sheet_name=sheet, header=None, index_col=0)
            df.at["allowPVCurtailment",df.columns[0]] = int(pv.get("can_curtail"))

        if sheet == "WindGeneratorPar" and wind != None:
            df = pandas.read_excel(base_file, sheet_name=sheet, header=None, index_col=0)
            df.at["WindRateCapacity",df.columns[0]] = 50 #using fixed capacity per wind generator unit for calculation purposes
            df.at["WindCapitalCost",df.columns[0]] = 50 * wind.get("installed_cost_per_kw")
            df.at["WindLifeTime",df.columns[0]] = wind.get("macrs_option_years")

        if sheet == "WindGeneratorForcedInvest" and wind != None:
            df = pandas.read_excel(base_file, sheet_name=sheet, header=None, index_col=0)
            df = set_invest(df, "node1", wind.get("min_kw"), 0, wind.get("max_kw"))

        if sheet == "StorageCostParameters" and es != None:
            df = pandas.read_excel(base_file, sheet_name=sheet, index_col=0)
            hasHeader = True
            df.at["ElectricStorage","VariableCost"] = es.get("installed_cost_per_kw")
            #df.at["ElectricStorage","VariableOM"] = electricStorage.get("replace_cost_per_kwh") * 24 * 30
            df.at["ElectricStorage","Lifetime"] = es.get("battery_replacement_year")
            #df.at["maxs"] = electricStorage.get("max_kw") / 2000
            #df.at["capcost"] = electricStorage.get("replace_cost_per_kw")

        if sheet == "StorageInvestParameters" and es != None:
            df = pandas.read_excel(base_file, sheet_name=sheet, index_col=0)
            #hasHeader = True
            df = set_invest(df, "ElectricStorage",es.get("min_kw"),0,es.get("max_kw"))

        if sheet == "BattInverterParameters" and es != None:
            #choosing 2000kw inverter type to update (temporary)
            df = pandas.read_excel(base_file, sheet_name=sheet, index_col=0)
            hasHeader = True
            df.at["BattInverter_2000kw","Lifetime"] = es.get("inverter_replacement_year")

        if sheet == "ElecStorageStationaryParameter" and es != None:
            df = pandas.read_excel(base_file, sheet_name=sheet, header=None, index_col=0)
            df.at["DiscreteSize",df.columns[0]] = es.get("max_kwh")

        if sheet == "LFGenSetOPT" and generator != None:
            df = pandas.read_excel(base_file, sheet_name=sheet, index_col=0)
            df.at["LFGS01","capcost"] = generator.get("installed_cost_per_kw")
            df.at["LFGS01","OMFix"] = generator.get("om_cost_per_kw")
            df.at["LFGS01","lifetime"] = generator.get("macrs_option_years")
            df.at["LFGS01","BackupOnly"] = int(generator.get("only_runs_during_grid_outage"))
            df.at["LFGS01","Fuel"] = 4
            df.at["LFGS01","Type"] = 3

        if sheet == "EnableInvestment":
            df = pandas.read_excel(base_file, sheet_name=sheet, index_col=0)
            hasHeader = True
            df.at["node1","GenSetInvest"] = int(generator != None)
            df.at["node1","SolarInvest"] = int(pv != None)
            df.at["node1","StorageInvest"] = int(es != None)
            df.at["node1","WindInvest"] = int(wind != None)
        else:
            df = pandas.read_excel(base_file, sheet_name=sheet, header=None)
            hasIndex = False

        if create_new_file:
            df.to_excel(der_cam_file_path, sheet_name=sheet, index=hasIndex, header=hasHeader)
            create_new_file = False
        else:
            with pandas.ExcelWriter(der_cam_file_path, mode='a') as writer:
                df.to_excel(writer, sheet_name=sheet, index=hasIndex, header=hasHeader)

    print(f"successfully created der-cam input at {path}/{der_cam_file_name}")

#######################################################################
### functions for posting model to API and checking for model results
#######################################################################

def check_timeout(start_time, timeout):
    if timeout != 0:
        current_time = time.time()
        if current_time - start_time >= timeout:
            return True
    return False

def check_lock(lock_path, timeout):
    ''' checks if another API call is running and prints statement if so '''
    printed = False
    current_time = time.time()
    while os.path.exists(lock_path):
        if not printed:
            print("30 second wait required between DER-CAM API calls - waiting ...")
            printed = True
        if check_timeout(current_time, 30):
            print("30 seconds have passed: an error may be causing the lock file to not be released correctly")
        if check_timeout(current_time, timeout):
            print(f"error: timeout of {timeout} seconds reached while waiting for lock file to release")
            return 

def release_lock(start_time, lock_path):
    ''' waits for up to 30 seconds before releasing API lock to ensure that API limits are followed '''
    end_time = time.time()
    sleep_time = 30 - ( end_time - start_time )
    if sleep_time > 0:
        print(f'sleeping for {sleep_time} seconds')
        time.sleep(sleep_time)
    os.remove(lock_path)
    print("lock released")

def check_model_status( modelKey, userKey ):
    ''' checks status of posted model '''
    urlKey = f'{urlBase}/{userKey}/model/{modelKey}'
    response = req.get(urlKey)
    model = response.json()['model']
    return model['results_available'], model['status'], model['msg']

def get_model_results( modelKey, userKey, modelHasResults ):
    ''' accesses available results '''
    if modelHasResults == 1:
        urlResults = f'{urlBase}/{userKey}/model/{modelKey}/results'
        resultsResponse =  req.get(urlResults)
        return resultsResponse.json()['model']
    else:
        print(f"error: model results for key {modelKey} were not posted")

#todo: remove any print statements that aren't useful to the user
def solve_model(path, modelFile, timeout=0): 
    ''' 
    posts the model file to the DER-CAM API, waits to receive results, 
    saves results to testFiles/results.csv and testFiles/results_nodes.csv,
    and ensures total runtime of at least 30 seconds per call (to meet API limits)
    '''
    userKey = get_credentials()
    if userKey == None:
        userKey = set_credentials()

    modelFilePath = os.path.normpath(os.path.join(path, modelFile))
    files = {'modelFile': ('model.xlsx', open(modelFilePath, 'rb'), fileMimeType, {'Expires': '0'})}
    urlRequest = f'{urlBase}/{userKey}/model'
    data={ 'label': "example model post request", 'version': 5.9 }
    
    lock_path = os.path.normpath(os.path.join(thisDir,lock_file))
    check_lock(lock_path,timeout)
    
    if not os.path.exists(lock_path):
        with open(lock_path, 'w') as f:
            f.write(str(os.getpid()))
            print(f"lock acquired at: {lock_path}")
        #posts model to API
        response = req.post(url=urlRequest, data=data, files=files)
        start_time = time.time()
        print(f"response.status_code: {response.status_code}, response.reason: {response.reason}")
        modelResponse = response.json()['model']
        #acquires key for given model
        modelKey = modelResponse['model_key']

        modelHasResults, modelStatus, modelMsg = check_model_status( modelKey, userKey )
        if modelStatus == "failed":
            release_lock(start_time, lock_path)
            print(f"error: {modelMsg}")
            return 

        #waits for model to solve
        while modelHasResults != 1:
            #add waiting period between checks? (doesn't seem to have limits on requests, only posting models)
            modelHasResults, modelStatus, modelMsg = check_model_status( modelKey, userKey )
            if modelStatus == "failed":
                release_lock(start_time, lock_path)
                print(f"error: {modelMsg}")
                return
            if check_timeout(start_time, timeout):
                release_lock(start_time, lock_path)
                print(f"error: timeout of {timeout} seconds reached while waiting for model results")
                print(f"results available: {modelHasResults}, status: {modelStatus}, msg: {modelMsg}")
                return 

        solvedModel = get_model_results( modelKey, userKey, modelHasResults )
        
        #todo: add optional function inputs for output file names
        with open(os.path.normpath(os.path.join(path,"results.csv")), 'w') as f:
            f.write(solvedModel['results'])
            
        with open(os.path.normpath(os.path.join(path,"results_nodes.csv")), 'w') as f:
            f.write(solvedModel['resultsNodes'])

        print(f'model competed: results saved to {path}/results.csv and {path}/resultsNodes.csv')
        
        release_lock(start_time, lock_path)

def print_existing_models(userKey):
    ''' prints all existing models saved to the account associated with the specified API key '''
    response = req.get(f'{urlBase}/{userKey}/model')
    myModels = response.json()['models']
    print("existing models: ")
    print(myModels)


#def print_model( modelKey ):
#    ''' prints results from the model with the given API key if it exists in the users account '''

def run(path, modelFile="", reoptFile="", timeout=0):
    ''' 
    if reoptFile provided (json) : translates to der-cam input sheet and solves model 
    if modelFile provided (xlsx) : solves given modelFile
    '''
    if modelFile == "" and reoptFile == "":
        return "error: enter modelFile and/or reoptFile to translate into modelFile"
    elif modelFile == "":
        build_input_spreadsheet(path, reoptFile, "der_cam_inputs.xlsx")
        modelFile = "der_cam_inputs.xlsx"
    solve_model(path, modelFile, timeout=timeout)


def _test():
    run(os.path.normpath(os.path.join(thisDir,"testFiles")), modelFile="test.xlsx")

    #print_existing_models()

if __name__ == "__main__":
    _test()
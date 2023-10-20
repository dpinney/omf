from omf.solvers.reopt_jl import __init__ 

#for graphs
import matplotlib.pyplot as plt
import numpy as np

#for adding interactive graphs to html
import mpld3

##########################################
# functions for displaying REopt.jl output (currently used for testing)
##########################################

#generates html for microgrid overview given REopt.jl output json and resilience output json
def microgrid_overview_table(testName, json, outage_json=None):
    retStr = f'''<p>
    Recommended Microgrid Design Overview for {testName} <br>
    <table border=1px cellspacing=0>
    '''

    overview_vals = [None] * 9

    overview_vals[0] = ("Total Savings" , json.get('Financial',{}).get("npv",0) )
    load = json.get('ElectricLoad',{}).get("load_series_kw",0)
    overview_vals[1] = ("Average Load (kWh)", round(sum(load)/len(load),1))

    overview_vals[2] = ( "Total Solar (kW)", json.get('PV',{}).get('size_kw',0) )
    overview_vals[3] = ("Total Wind (kW)", json.get('Wind',{}).get('size_kw',0) )
    overview_vals[4] = ("Total Inverter (kW)", json.get('ElectricStorage',{}).get('size_kw',0) )
    overview_vals[5] = ("Total Storage (kWh)", json.get('ElectricStorage',{}).get('size_kwh',0) )
    overview_vals[6] = ("Total Fossil (kW)", json.get('Generator',{}).get('size_kw',0) )

    avgOutage = 0
    if outage_json:
        avgOutage = outage_json["resilience_hours_avg"]
    overview_vals[7] = ("Average length of survived Outage (hours)", avgOutage)

    #is this equivalent to REopt value?
    overview_vals[8] = ("Fossil Fuel consumed during specified Outage (diesel gal equiv)",
                         json.get('Generator',{}).get('annual_fuel_consumption_gal',0) )
    # generator_fuel_used_per_outage_gal? check source code

    headers = ""
    values = ""
    for (header, value) in overview_vals:
        headers += "<th> " + header + "</th>"
        values += "<td>" + str(value) + "</td>"
    retStr += "<tr>" + headers + "</tr> <tr>" + values + "</tr></table></p>"

    return retStr

#generates html for financial performance given REopt.jl output json
def financial_performance_table(testName, json):
    retStr = f''' <p>
    Microgrid Lifetime Financial Performance for {testName} <br>
    <table border=1px cellspacing=0>
    '''
    h = [ ["", "Business as Usual", "Microgrid", "Difference"],
         ["Demand Cost", "", "", ""],
         ["Energy Cost", "", "", ""],
         ["Total Cost", "", "", ""] ]
    
    et = json.get(('ElectricTariff'),{})
    f = json.get('Financial',{})

    #todo: round all to 2 decimals [ round(val, 2) ]
    h[1][1] = et.get("lifecycle_demand_cost_after_tax_bau")
    h[1][2] = et.get("lifecycle_demand_cost_after_tax")
    h[1][3] = h[1][1] - h[1][2]
    h[2][1] = et.get("lifecycle_energy_cost_after_tax_bau")
    h[2][2] = et.get("lifecycle_energy_cost_after_tax")
    h[2][3] = h[2][1] - h[2][2]
    h[3][1] = f.get("lcc_bau")
    h[3][2] = f.get("lcc")
    h[3][3] = h[3][1] - h[3][2]
    
    for i in range(4):
        retStr += "<tr>"
        for j in range(4):
            isHeader = i == 0 or j == 0
            retStr += "<th>" if isHeader else "<td>"
            retStr += str(h[i][j])
            retStr += "</th>" if isHeader else "</td>"
        retStr += "</tr>"

    retStr += "</table></p>"
    return retStr

#todo: generate html for proforma analysis given REopt.jl output json
def proforma_table(json):
    retStr = '''<p>
    <table border=1px cellspacing=0>
    '''
    retStr += "</table></p>"
    return retStr

#displays graph given output data from REopt.jl
def make_graph(x,ys,xlabel,ylabel,title):
    fig, ax = plt.subplots(figsize=(10, 6))
    containsLabels = False
    for (y,label) in ys:
        if label == "":
            ax.plot(x,y)
        else:
            ax.plot(x, y, label=label)
            containsLabels = True
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if containsLabels:
        plt.legend()
    plt.grid(True)
    return (fig, ax)

def all_graphs(json, outage_json):
    retStr = ""

    electricUtility = json.get('ElectricUtility',{})
    pv = json.get('PV',{})
    wind = json.get('Wind',{})
    electricStorage = json.get('ElectricStorage',{})
    generator = json.get('Generator',{})

    load_overview = []
    battery_charge_source = []
    
    x = np.arange(8760) #8760 = hours in a year

    if electricStorage:
        load_overview.append((electricStorage['storage_to_load_series_kw'], "Battery to Load"))
        battery_charge_percentage = [ (electricStorage['soc_series_fraction'],'') ]

        (fig_batt_percent,ax_batt_percent) = make_graph(x, battery_charge_percentage,"time","%", 
                                                  "Battery Charge Percentage")
        
    if pv:
        load_overview.append((pv['electric_to_load_series_kw'], "PV to Load"))
        battery_charge_source.append((pv['electric_to_storage_series_kw'], "Solar"))

        solar_generation = [(pv['electric_to_load_series_kw'], "PV used to meet Load")]
        solar_generation.append((pv['electric_curtailed_series_kw'], "PV Curtailed"))
        solar_generation.append((pv['electric_to_grid_series_kw'], "PV exported to Grid"))
        solar_generation.append((pv['electric_to_storage_series_kw'], "PV used to charge Battery"))

        (fig_pv,ax_pv) = make_graph(x, solar_generation,"time","Power (kW)","Solar Generation")
        retStr += mpld3.fig_to_html(fig_pv)
        plt.close(fig_pv)

    if electricUtility:
        load_overview.append((electricUtility['electric_to_load_series_kw'], "Grid to Load"))
        battery_charge_source.append((electricUtility['electric_to_storage_series_kw'], "Grid"))

    if wind:
        load_overview.append((wind['electric_to_load_series_kw'], "Wind to Load"))
        battery_charge_source.append((wind['electric_to_storage_series_kw'], "Wind"))

        wind_generation = [ (wind['electric_to_load_series_kw'], "Wind used to meet Load") ]
        wind_generation.append((wind['electric_to_storage_series_kw'], "Wind used to charge Battery"))

        (fig_wind,ax_wind) = make_graph(x, wind_generation,"time","Power (kW)","Wind Generation")
        retStr += mpld3.fig_to_html(fig_wind)
        plt.close(fig_wind)

    if generator:
        load_overview.append((generator['electric_to_load_series_kw'], "Generator to Load"))
        battery_charge_source.append((generator['electric_to_storage_series_kw'], "Fossil Gen"))
        
        fossil_generation = [ (generator['electric_to_load_series_kw'],"Fossil Gen used to meet Load") ]
        fossil_generation.append((generator['electric_to_storage_series_kw'],
                                  "Fossil Gen used to charge Battery"))

        (fig_fossil,ax_fossil) = make_graph(x, fossil_generation,"time","Power (kW)","Fossil Generation")
        retStr += mpld3.fig_to_html(fig_fossil)
        plt.close(fig_fossil)

    (fig_load,ax_load) = make_graph(x, load_overview,"time","Power (kW)","Load Overview")
    retStr = mpld3.fig_to_html(fig_load) + retStr
    plt.close(fig_load)

    if electricStorage:
        (fig_batt_source,ax_batt_source) = make_graph(x, battery_charge_source,"time","Power (kW)",
                                                  "Battery Charge Source")
        retStr += mpld3.fig_to_html(fig_batt_source)
        retStr += mpld3.fig_to_html(fig_batt_percent)
        plt.close(fig_batt_source)
        plt.close(fig_batt_percent)

    if outage_json != None:

        resilience = outage_json["resilience_by_time_step"]
        res_y = [(resilience,"")]
        res_x = np.arange(len(resilience))
        (fig_res,ax_res) = make_graph(res_x, res_y, "Start Hour", "Longest Outage Survived (hours)",
                                      "Resilience Overview")
        retStr += mpld3.fig_to_html(fig_res)
        plt.close(fig_res)

        survival_prob_x = outage_json["outage_durations"]
        survival_prob_y = [(outage_json["probs_of_surviving"], "")]

        (fig_survival, ax_survival) = make_graph(survival_prob_x, survival_prob_y, "Outage Length (hours)",
                                                "Probability of Meeting Critical Load", 
                                                "Outage Survival Probability")
        retStr += mpld3.fig_to_html(fig_survival)
        plt.close(fig_survival)

    return retStr


#displays results of REopt.jl call in html file
def display_julia_output_json(filepath, total_runtime, outage_output=""):
    output_json = __init__.get_json(filepath)
    #outage_output = __init__.get_json(filepath + "_outages")

    html_graphs = all_graphs(output_json, outage_output)

    html_doc = f'''
    <body>
    <p>
    <b>Total runtime: {total_runtime} seconds</b>
    </p>
    {microgrid_overview_table(output_json,outage_output)}
    {financial_performance_table(output_json)}
    '''
    html_doc += html_graphs + "</body>"
    #to do: different output files based on test name
    Html_file= open("testFiles/sample_test.html","w")
    Html_file.write(html_doc)
    Html_file.close()


def get_test_overview(testPath, runtime, solver, simulate_outages):
    tab = "&nbsp;"
    retStr = "<p>"
    retStr += "Test File: " + testPath + "<br>"
    retStr += tab + "Runtime: " + str(runtime) + "<br>"
    retStr += tab + "Solver: " + solver + "<br>"
    retStr += tab + "Simulates outages? "
    retStr += "Yes <br></p>" if simulate_outages else "No <br></p>"
    return retStr

def compareTimesHeader():
    return '''
    <table border=1px cellspacing=0>
    <tr>
        <th> Test Name </th>
        <th> Solver </th>
        <th> Runtime </th>
    </tr>
    '''

def compareTimesRow(name, solver, runtime):
    return f'''
    <tr>
        <td> {name} </td>
        <td> {solver} </td>
        <td> {runtime} </td>
    </tr>
    '''
    

#for comparing mutiple test outputs
# tests = [ (testPath, runtime, solver, simulate_outages ), ... ]
def html_comparison(test_list):
    html_doc = "<body>"
    overview_str = ""
    timing_str = compareTimesHeader()
    microgrid_overview_str = ""
    financial_performance_str = ""
    graphs = []

    for (testPath, outagePath, testName, runtime, solver, simulate_outages, get_cached) in test_list:

        if get_cached:
            runtime = "N/A: cached test"

        timing_str += compareTimesRow(testName, solver, runtime)

        overview_str += get_test_overview(testPath,runtime,solver,simulate_outages)

        output_json = __init__.get_json(testPath)
        outage_json = __init__.get_json(outagePath)
        test = testName + " ( solver: " + solver + " )"

        microgrid_overview_str += microgrid_overview_table(test, output_json, outage_json)
        financial_performance_str += financial_performance_table(test, output_json)

        graph_set = all_graphs(output_json, outage_json)
        graphs.append((graph_set,test))

    timing_str += "</table><br><br>"
    html_doc += timing_str + overview_str + microgrid_overview_str + financial_performance_str
    for (graph,test) in graphs:
        html_doc += "<p> graphs for " + test + "<br>"
        html_doc += graph + "</p>"

    html_doc += "</body>"
    html_file= open("testFiles/sample_comparison_test.html","w")
    html_file.write(html_doc)
    html_file.close()
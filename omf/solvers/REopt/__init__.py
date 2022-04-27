import json
import requests
from omf.solvers.REopt import logger
from omf.solvers.REopt import results_poller

def run(inJSONPath, outputPath):
	API_KEY = 'WhEzm6QQQrks1hcsdN0Vrd56ZJmUyXJxTJFg6pn9'  # OMF KEY. REPLACE WITH YOUR API KEY
	# API_KEY = 'Y8GMAFsqcPtxhjIa1qfNj5ILxN5DH5cjV3i6BeNE'
	# API_KEY = 'etg8hytwTYRf4CD0c4Vl9U7ACEQnQg6HV2Jf4E5W'
	# API_KEY = 'BNFaSCCwz5WkauwJe89Bn8FZldkcyda7bNwDK1ic'		 
	# API_KEY = 'L2e5lfH2VDvEm2WOh0dJmzQaehORDT8CfCotaOcf'
	# API_KEY = '08USmh2H2cOeAuQ3sCCLgzd30giHjfkhvsicUPPf'
	root_url = 'https://developer.nrel.gov/api/reopt'
	post_url = root_url + '/v1/job/?api_key=' + API_KEY
	results_url = root_url + '/v1/job/<run_uuid>/results/?api_key=' + API_KEY
	post = json.load(open(inJSONPath))
	resp = requests.post(post_url, json=post)
	if not resp.ok:
		logger.log.error("Status code {}. {}".format(resp.status_code, resp.content))
	else:
		logger.log.info("Response OK from {}.".format(post_url))
		run_id_dict = json.loads(resp.text)
		try:
			run_id = run_id_dict['run_uuid']
		except KeyError:
			msg = "Response from {} did not contain run_uuid.".format(post_url)
			logger.log.error(msg)
			raise KeyError(msg)
		results = results_poller.poller(url=results_url.replace('<run_uuid>', run_id))
		with open(outputPath, 'w') as fp:
			json.dump(obj=results, fp=fp, indent=4)
		logger.log.info("Saved results to {}".format(outputPath))

def runResilience(runID, outputPath):
	API_KEY = 'WhEzm6QQQrks1hcsdN0Vrd56ZJmUyXJxTJFg6pn9'  # OMF KEY. REPLACE WITH YOUR API KEY
	# API_KEY = 'Y8GMAFsqcPtxhjIa1qfNj5ILxN5DH5cjV3i6BeNE'
	# API_KEY = 'etg8hytwTYRf4CD0c4Vl9U7ACEQnQg6HV2Jf4E5W'
	# API_KEY = 'BNFaSCCwz5WkauwJe89Bn8FZldkcyda7bNwDK1ic'
	# API_KEY = 'L2e5lfH2VDvEm2WOh0dJmzQaehORDT8CfCotaOcf'
	# API_KEY = '08USmh2H2cOeAuQ3sCCLgzd30giHjfkhvsicUPPf'
	root_url = 'https://developer.nrel.gov/api/reopt'
	post_url = root_url + '/v1/outagesimjob/?api_key=' + API_KEY
	results_url = root_url + '/v1/job/<RUN_ID>/resilience_stats/?api_key=' + API_KEY
	resp = requests.post(post_url, json={'run_uuid':runID, 'bau':False})
	if not resp.ok:
		logger.log.error("Status code {}. {}".format(resp.status_code, resp.content))
	else:
		logger.log.info("Response OK from {}.".format(post_url))
		run_id_dict = json.loads(resp.text)
		print(resp.text)
		try:
			run_id = run_id_dict['run_uuid']
		except KeyError:
			msg = "Response from {} did not contain run_uuid.".format(post_url)
			logger.log.error(msg)
			raise KeyError(msg)
		results = results_poller.rez_poller(url=results_url.replace('<RUN_ID>', run_id))
		with open(outputPath, 'w') as fp:
			if "outage_sim_results" in results:
				json.dump(obj=results["outage_sim_results"], fp=fp, indent=4)
			else:
				error_dict = {"Error":str(results['Error'])}
				json.dump(obj=error_dict, fp=fp, indent=4)
				logger.log.info("Warning: Response from {} did not contain outage_sim_results. Resilience metrics will not be included.".format(results_url))
		logger.log.info("Saved results to {}".format(outputPath))

def _test():
	run('Scenario_POST72.json', 'results_S72.json')

	with open('results_S72.json') as jsonFile:
		results = json.load(jsonFile)
		
	test_ID = results['outputs']['Scenario']['run_uuid']
	print("PV size_kw:", results['outputs']['Scenario']['Site']['PV']['size_kw'])
	print("Storage size_kw:", results['outputs']['Scenario']['Site']['Storage']['size_kw'])
	print("Storage size_kwh:", results['outputs']['Scenario']['Site']['Storage']['size_kwh'])
	# print("Wind size_kw:", results['outputs']['Scenario']['Site']['Wind']['size_kw'])
	print("Generator fuel_used_gal:", results['outputs']['Scenario']['Site']['Generator']['fuel_used_gal'])
	print("Generator fuel_used_gal_bau:", results['outputs']['Scenario']['Site']['Generator']['fuel_used_gal_bau'])
	print("Generator size_kw:", results['outputs']['Scenario']['Site']['Generator']['size_kw'])
	print("Generator average_yearly_energy_produced_kwh:", results['outputs']['Scenario']['Site']['Generator']['average_yearly_energy_produced_kwh'])
	print("Generator average_yearly_energy_exported_kwh:", results['outputs']['Scenario']['Site']['Generator']['average_yearly_energy_exported_kwh'])
	print("Generator existing_gen_total_fuel_cost_us_dollars:", results['outputs']['Scenario']['Site']['Generator']['existing_gen_total_fuel_cost_us_dollars'])
	print("Generator year_one_emissions_lb_C02:", results['outputs']['Scenario']['Site']['Generator']['year_one_emissions_lb_C02'])
	print("Generator year_one_emissions_bau_lb_C02:", results['outputs']['Scenario']['Site']['Generator']['year_one_emissions_bau_lb_C02'])
	print("npv_us_dollars:", results['outputs']['Scenario']['Site']['Financial']['npv_us_dollars'])
	print("initial_capital_costs:", results['outputs']['Scenario']['Site']['Financial']['initial_capital_costs'])
	# print("CHP size_kw:", results['outputs']['Scenario']['Site']['CHP']['size_kw'])
	# print("CHP year_one_fuel_used_mmbtu:", results['outputs']['Scenario']['Site']['CHP']['year_one_fuel_used_mmbtu'])
	# print("CHP year_one_electric_energy_produced_kwh:", results['outputs']['Scenario']['Site']['CHP']['year_one_electric_energy_produced_kwh'])

	# runResilience(test_ID, 'resultsResilience_S40.json')



if __name__ == '__main__':
	_test()

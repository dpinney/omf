import json
import requests
from omf.solvers.REopt import logger
from omf.solvers.REopt import results_poller

def run(inJSONPath, outputPath):
	API_KEY = 'WhEzm6QQQrks1hcsdN0Vrd56ZJmUyXJxTJFg6pn9'  # REPLACE WITH YOUR API KEY
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
	API_KEY = 'WhEzm6QQQrks1hcsdN0Vrd56ZJmUyXJxTJFg6pn9'  # REPLACE WITH YOUR API KEY
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
			json.dump(obj=results["outage_sim_results"], fp=fp, indent=4)
		logger.log.info("Saved results to {}".format(outputPath))

def _test():
	run('Scenario_POST13.json', 'results_S13.json')

	with open('results_S13.json') as jsonFile:
		results = json.load(jsonFile)
		
	test_ID = results['outputs']['Scenario']['run_uuid']
	print("PV size_kw:", results['outputs']['Scenario']['Site']['PV']['size_kw'])
	print("Storage size_kw:", results['outputs']['Scenario']['Site']['Storage']['size_kw'])
	print("Storage size_kwh:", results['outputs']['Scenario']['Site']['Storage']['size_kwh'])
	print("Wind size_kw:", results['outputs']['Scenario']['Site']['Wind']['size_kw'])
	print("Generator fuel_used_gal:", results['outputs']['Scenario']['Site']['Generator']['fuel_used_gal'])
	print("Generator size_kw:", results['outputs']['Scenario']['Site']['Generator']['size_kw'])
	print("npv_us_dollars:", results['outputs']['Scenario']['Site']['Financial']['npv_us_dollars'])
	runResilience(test_ID, 'resultsResilience_S13.json')



if __name__ == '__main__':
	_test()

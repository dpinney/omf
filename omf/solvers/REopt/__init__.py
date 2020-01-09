import json
import requests
import omf.solvers.REopt.logger as logger
import omf.solvers.REopt.results_poller as results_poller

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
	results_url = root_url + '/v1/job/' + runID +'/resilience_stats/?api_key=' + API_KEY

	resp = requests.get(results_url)

	if not resp.ok:
		logger.log.error("Status code {}. {}".format(resp.status_code, resp.content))
	else:
		logger.log.info("Response OK from {}.".format(results_url))
		respDict = json.loads(resp.text)

	with open(outputPath, 'w') as fp:
		json.dump(obj=respDict, fp=fp, indent=4)

	logger.log.info("Saved results to {}".format(outputPath))


def _test():
	run('Scenario_test_POST.json', 'results.json')

if __name__ == '__main__':
	_test()

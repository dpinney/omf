import requests
import json
from logger import log
from results_poller import poller

def run(inJSONPath, outputPath):
	API_KEY = 'WhEzm6QQQrks1hcsdN0Vrd56ZJmUyXJxTJFg6pn9'  # REPLACE WITH YOUR API KEY

	root_url = 'https://developer.nrel.gov/api/reopt'
	post_url = root_url + '/v1/job/?api_key=' + API_KEY
	results_url = root_url + '/v1/job/<run_uuid>/results/?api_key=' + API_KEY

	post = json.load(open(inJSONPath))

	resp = requests.post(post_url, json=post)

	if not resp.ok:
		log.error("Status code {}. {}".format(resp.status_code, resp.content))
	else:
		log.info("Response OK from {}.".format(post_url))
		run_id_dict = json.loads(resp.text)

		try:
			run_id = run_id_dict['run_uuid']
		except KeyError:
			msg = "Response from {} did not contain run_uuid.".format(post_url)
			log.error(msg)
			raise KeyError(msg)

		results = poller(url=results_url.replace('<run_uuid>', run_id))
		with open(outputPath, 'w') as fp:
			json.dump(obj=results, fp=fp, indent=4)

		log.info("Saved results to {}".format(outputPath))


def _test():
	run('Scenario_test_POST.json', 'results.json')

if __name__ == '__main__':
	_test()
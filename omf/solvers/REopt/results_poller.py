"""
function for polling reopt api results url
"""
import json, time
import requests
from omf.solvers.REopt import logger


def poller(url, poll_interval=2):
    """
    Function for polling the REopt API results URL until status is not "Optimizing..."
    :param url: results url to poll
    :param poll_interval: seconds
    :return: dictionary response (once status is not "Optimizing...")
    """
    key_error_count = 0
    key_error_threshold = 4
    status = "Optimizing..."
    logger.log.info("Polling {} for results with interval of {}s...".format(url, poll_interval))
    while True:

        resp = requests.get(url=url)
        resp_dict = json.loads(resp.text)

        try:
            status = resp_dict['outputs']['Scenario']['status']
        except KeyError:
            key_error_count += 1
            logger.log.info('KeyError count: {}'.format(key_error_count))
            if key_error_count > key_error_threshold:
                logger.log.info('Breaking polling loop due to KeyError count threshold of {} exceeded.'
                         .format(key_error_threshold))
                break

        if status != "Optimizing...":
            break
        else:
            time.sleep(poll_interval)

    return resp_dict

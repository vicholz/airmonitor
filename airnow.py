#!/usr/bin/env python3
import json
import logging
import requests
import urllib3
import os
from collections import defaultdict

try:
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass

AIRNOW_URL = "https://www.airnowapi.org/aq/observation/zipCode/current/?format=application/json&zipCode={zipcode}&distance={distance}&API_KEY={api_key}"

class Airnow:
    def __init__(self, api_key=os.environ.get('AIRNOW_API_KEY')):
        self.api_key = api_key
        self.session = requests.session()
        self.session.verify = False
        if not self.api_key:
            raise Exception("No Airnow API key specified or found in AIRNOW_API_KEY env variable.")
        try:
            logging.config.fileConfig("logging.conf")
        except:
            pass
        if os.environ.get("DEBUG"):
            logging.getLogger().setLevel(logging.DEBUG)
    
    def get_raw_data(self, zipcode, distance=25):
        logging.debug("Getting results...")
        URL = AIRNOW_URL.format(**locals(), api_key=self.api_key)
        data = self.session.get(URL).json()
        logging.debug(data)
        return data
    
    def get_data(self, zipcode, distance=25):
        logging.debug("Getting data from results...")
        data = self.get_raw_data(zipcode, distance)
        results = defaultdict(dict)
        for result in data:
            results[result['ParameterName']] = defaultdict(dict)
            results[result['ParameterName']]['AQI'] = result['AQI']
            results[result['ParameterName']]['index'] = result['Category']['Number']
        return results

if __name__ == "__main__":
    airnow = Airnow()
    data = airnow.get_data("94521")

    with open('airnow_data.json', 'w+') as f:
        f.write(json.dumps(data, sort_keys=True, indent=4))
    exit(0)

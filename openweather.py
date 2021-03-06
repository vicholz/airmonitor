#!/usr/bin/env python3
import json
import logging
import requests
import os
from decouple import config

try:
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather?q={zipcode}&appid={api_key}&units=imperial"

class OpenWeather:
    def __init__(self, api_key=config('OPENWEATHER_API_KEY')):
        self.api_key = api_key
        self.session = requests.session()
        self.session.verify = False
        if not self.api_key:
            raise Exception("No OpenWeather API key specified or found in OPENWEATHER_API_KEY env variable.")
    
    def get_raw_data(self, zipcode):
        URL = OPENWEATHER_URL.format(**locals(), api_key=self.api_key)
        data = self.session.get(URL).json()
        logging.debug(data)
        return data

    def get_data(self, zipcode):
        data = self.get_raw_data(zipcode)
        return data["main"]["feels_like"]
        

if __name__ == "__main__":
    ow = OpenWeather()
    data = ow.get_data("94521")

    with open('openweather_data.json', 'w+') as f:
        f.write(json.dumps(data, sort_keys=True, indent=4))
    exit(0)

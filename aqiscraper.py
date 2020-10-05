#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import re
import shutil
import socket
import sys
import time
import unittest

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome import service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.airnow.gov/?city=Concord&state=CA&country=USA"
AQI_XPATH = "//div[@class='aqi']/b"
TEMP_XPATH = "//div[@class='weather-value']"

#https://download-chromium.appspot.com/
CHROME_BINARY_FILEPATH = 'Chromium.app'

os.environ['MOZ_HEADLESS'] = '1'
os.environ['DISPLAY'] = ':0'

service_args = [
    '--ssl-protocol=any',
    '--ignore-ssl-errors=true'
]

preferences = {
    "webrtc.ip_handling_policy" : "disable_non_proxied_udp",
    "webrtc.multiple_routes_enabled": False,
    "webrtc.nonproxied_udp_enabled" : False
}

class AQIScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_experimental_option("prefs", preferences)
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('window-size=1920x1080')
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-impl-side-painting")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--disable-seccomp-filter-sandbox")
        chrome_options.add_argument("--disable-breakpad")
        chrome_options.add_argument("--disable-client-side-phishing-detection")
        chrome_options.add_argument("--disable-cast")
        chrome_options.add_argument("--disable-cast-streaming-hw-encoding")
        chrome_options.add_argument("--disable-cloud-import")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-session-crashed-bubble")
        chrome_options.add_argument("--disable-ipv6")
        chrome_options.add_argument("--allow-http-screen-capture")
        chrome_options.add_argument('--user-agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4274.0 Safari/537.36"')
        self.driver = webdriver.Chrome(
            options=chrome_options,
            service_args=service_args,
            service_log_path="selenium.log",
            # executable_path=CHROME_BINARY_FILEPATH
        )
        # self.driver = webdriver.PhantomJS(service_args=service_args, service_log_path='aqi_driver.log')
        self.driver.implicitly_wait(30)
    
    def get_data(self, url=URL):
        self.driver.get(url)
        self.driver.save_screenshot("load.png")
        
        aqi = WebDriverWait(self.driver, 30).until(
        EC.presence_of_element_located((By.XPATH, AQI_XPATH)))
        temp = WebDriverWait(self.driver, 30).until(
        EC.presence_of_element_located((By.XPATH, TEMP_XPATH)))

        return { 
            "aqi": int(aqi.get_property('textContent')),
            "temp": int(temp.get_property('textContent')),
            "timestamp": datetime.datetime.now().timestamp(),
            "status": "GOOD" if aqi.get_status(data["aqi"], data["temp"]) else "BAD"
        }
    
    def get_status(self, aqi, temp):
        if aqi > 50 or temp > 75:
            return False
        else:
            return True

    def tearDown(self):
        self.driver.quit()

if __name__ == "__main__":
    aqi_scraper = AQIScraper()
    data = aqi_scraper.get_data()
    aqi_scraper.tearDown()

    with open('aqi_data.json', 'w+') as f:
        f.write(json.dumps(data, sort_keys=True, indent=4))
    exit(0)

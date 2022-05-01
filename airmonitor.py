#!/usr/bin/env python3
import json
import os
import logging
import datetime
import sys
from logging import handlers
from collections import defaultdict
from airnow import Airnow
from openweather import OpenWeather
from mailchimp3 import MailChimp
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class AirMonitor:
    def __init__(self):
        self.state = defaultdict(dict)

    def load_previous_state(self, file="airmonitor_data.json"):
        if os.path.isfile(file):
            logging.info("Loading previous state '{file}'...".format(**locals()))
            with open(file, 'r') as f:
                state = json.load(f)
                self.previous_state = state
                state_string = json.dumps(state, sort_keys=True, indent=4)
                logging.debug("Previous state: \n {state_string}".format(**locals()))
                logging.info("Loading previous state '{file}'...DONE!".format(**locals()))
                return self.previous_state
        else:
            self.previous_state = defaultdict(dict)
            return self.previous_state
    
    def save_state(self, file="airmonitor_data.json"):
        logging.info("Saving current state '{file}'...".format(**locals()))
        self.state['timestamp'] = datetime.datetime.now().timestamp()
        with open(file, 'w') as f:
            f.write(json.dumps(self.state, sort_keys=True, indent=4))
        state_string = json.dumps(self.state, sort_keys=True, indent=4)
        logging.debug("Saved state: \n {state_string}".format(**locals()))
        logging.info("Saving current state '{file}'...DONE!".format(**locals()))

    def get_aqi_data(self, zipcode=os.environ.get('ZIPCODE')):
        logging.info("Getting AQI data for {zipcode}...".format(**locals()))
        airnow = Airnow()
        aqi_data = airnow.get_data(zipcode)
        logging.debug("AirNow Data: {aqi_data}".format(**locals()))
        self.state["aqi"] = aqi_data
        logging.info("Getting AQI data for {zipcode}...DONE!".format(**locals()))

    def get_weather_data(self, zipcode=os.environ.get('ZIPCODE')):
        logging.info("Getting weather data for {zipcode}...".format(**locals()))
        ow = OpenWeather()
        weather_data = ow.get_data(zipcode)
        logging.debug("Weather Data: {weather_data}".format(**locals()))
        self.state["temp"] = weather_data
        logging.info("Getting weather data for {zipcode}...DONE!".format(**locals()))
    
    def get_status(self, state, max_temp=75, max_index=1):
        if all([
            state.get('aqi'),
            state.get('temp')
        ]):
            if any([
                state.get('aqi').get('PM2.5').get('index') > max_index,
                state.get('aqi').get('O3').get('index') > max_index,
                state.get('temp') > max_temp
            ]):
                return True
            else:
                return False
        else:
            return False

    def compare_states(self):
        previous_status = self.get_status(self.previous_state)
        current_status = self.get_status(self.state)
        logging.debug("previous_status: {previous_status}".format(**locals()))
        logging.debug("current_status: {current_status}".format(**locals()))

        if current_status and not previous_status: return 1
        if current_status == previous_status: return 0
        if not current_status and previous_status: return -1

    def notify_mailchimp(self, state, campaign_id=os.environ.get('MAILCHIMP_CHAMPAIGN_ID')):
        client = MailChimp(os.environ.get('MAILCHIMP_API_KEY'))
        # print(client.campaigns.content.get(campaign_id=campaign_id))
        client.campaigns.actions.pause(campaign_id=campaign_id)
        client.campaigns.content.update(campaign_id=campaign_id, data={
            'plain_text': 'this is another test',
            'subject': 'test subject'
        })
        client.campaigns.actions.send(campaign_id=campaign_id)
        # client.campaigns.send(campaign_id)
    
    def notify_sendgrid(self, subject, message, recipients, from_email, api_key=os.environ.get('SENDGRID_API_KEY')):
        message = Mail(
            from_email=from_email,
            to_emails=recipients,
            subject=subject,
            html_content=message)
        try:
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(message)
            logging.info("Notification sent.")
            logging.debug(response.status_code)
            logging.debug(response.body)
            logging.debug(response.headers)
        except Exception as e:
            logging.error(str(e))
            exit(1)


if __name__ == "__main__":
    log_level = logging.INFO
    if os.environ.get("DEBUG", "FALSE") ==  "TRUE":
        log_level = logging.DEBUG

    log_format = logging.Formatter("%(asctime)s - %(process)s - %(name)s - %(levelname)s - [%(module)s]: %(message)s")

    logging.basicos.environ.get(
        format="%(asctime)s - %(process)s - %(name)s - %(levelname)s - [%(module)s]: %(message)s",
        filemode='a',
        level=log_level,
        datefmt='%Y/%m/%d %H:%M:%S'
    )
    rotating_file_handler = handlers.RotatingFileHandler(
        sys.argv[0].split("/")[-1].split(".")[0]+".log",
        maxBytes=(1048576*25), backupCount=5
    )
    rotating_file_handler.setFormatter(log_format)
    logging.getLogger().addHandler(rotating_file_handler)

    airmon = AirMonitor()
    airmon.load_previous_state()
    airmon.get_aqi_data()
    airmon.get_weather_data()
    state = airmon.compare_states()
    logging.debug("state:", state)
    logging.debug("data:\n", json.dumps(airmon.state, sort_keys=True, indent=4))
    recipients = [(x,x) for x in os.environ.get("RECIPIENTS").split(",")]
    if state == 1:
        logging.info("State changed: GOOD->BAD")
        airmon.notify_sendgrid(
            from_email=os.environ.get("FROM_EMAIL"),
            recipients=recipients,
            subject="AQI STATUS: BAD - AQI OR TEMP OUT OF DESIRED RANGE.",
            message="""
PM2.5: {pm25}<br>
O3: {o3}<br>
Temp: {temp}<br>
""".format(pm25=airmon.state['aqi']['PM2.5']['AQI'], o3=airmon.state['aqi']['O3']['AQI'], temp=airmon.state['temp'])
        )
    elif state == -1:
        logging.info("State changed: BAD->GOOD")
        airmon.notify_sendgrid(
            from_email=os.environ.get("FROM_EMAIL"),
            recipients=recipients,
            subject="AQI STATUS: GOOD - AQI OR TEMP IS WITHIN DESIRED RANGE.",
            message="""
PM2.5: {pm25}<br>
O3: {o3}<br>
Temp: {temp}<br>
""".format(pm25=airmon.state['aqi']['PM2.5']['AQI'], o3=airmon.state['aqi']['O3']['AQI'], temp=airmon.state['temp'])
        )
    airmon.save_state()
    exit(0)

pipeline {
    agent any
    options {
        buildDiscarder(logRotator(numToKeepStr: '10', artifactNumToKeepStr: '10'))
        ansiColor('xterm')
        timestamps()
    }
    triggers {
        cron('30 * * * *')
    }
    stages {
        stage ('AirMonitor - Checkout') {
            steps {
                checkout([$class: 'GitSCM', branches: [[name: '**']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '', url: 'https://github.com/vicholz/airmonitor']]])
            }
        }
        stage ('AirMonitor - Run') {
            steps {
                withCredentials([
                string(credentialsId: 'AIRNOW_API_KEY', variable: 'AIRNOW_API_KEY'),
                string(credentialsId: 'SENDGRID_API_KEY', variable: 'SENDGRID_API_KEY'),
                string(credentialsId: 'OPENWEATHER_API_KEY', variable: 'OPENWEATHER_API_KEY'),
                string(credentialsId: 'MAILCHIMP_API_KEY', variable: 'MAILCHIMP_API_KEY'),
                string(credentialsId: 'MAILCHIMP_CHAMPAIGN_ID', variable: 'MAILCHIMP_CHAMPAIGN_ID'),
                string(credentialsId: 'ZIPCODE', variable: 'ZIPCODE'),
                string(credentialsId: 'FROM_EMAIL', variable: 'FROM_EMAIL'),
                string(credentialsId: 'RECIPIENTS', variable: 'RECIPIENTS'),
            ]) {
                    sh '''
set +x
echo "AIRNOW_API_KEY=${AIRNOW_API_KEY}" > .env
echo "SENDGRID_API_KEY=${SENDGRID_API_KEY}" >> .env
echo "OPENWEATHER_API_KEY=${OPENWEATHER_API_KEY}" >> .env
echo "MAILCHIMP_API_KEY=${MAILCHIMP_API_KEY}" >> .env
echo "MAILCHIMP_CHAMPAIGN_ID=${MAILCHIMP_CHAMPAIGN_ID}" >> .env
echo "FROM_EMAIL=${FROM_EMAIL}" >> .env
echo "RECIPIENTS=${RECIPIENTS}" >> .env

python3 airmonitor.py
export PM25=$(jq '.aqi."PM2.5".AQI' airmonitor_data.json)
export O3=$(jq '.aqi."O3".AQI' airmonitor_data.json)
export TEMP=$(jq '.temp' airmonitor_data.json)

MESSAGE="PM2.5: ${PM25} - 03: ${O3} - TEMP: ${TEMP}F"
echo "MESSAGE='${MESSAGE}'" > build.properties
                    '''
                }
                script {
                    def props = readProperties file: 'build.properties'
                    currentBuild.displayName = "#${currentBuild.number} - ${props.MESSAGE}"
                }
            }
        }
    }
}
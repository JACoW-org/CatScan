# Jacow Validator's Deployment

June 21

## Where

The project is deployed on a VM at the Australia Synchrotron

## Getting access

Password are in rattic

## Updating

1. Login to the server
2. cd /home/jacow_user/jacow-validator
3. git pull origin master
4. docker kill $(docker ps -q)   # Will stop the app and db docker containers
5. docker-compose up --detach --build

## spms csv file

Previously, when it was running on amazon, a cron job was set up to run every hour to automatically download the csv file
from the [official jacow website](http://www.jacow.org/) to keep locally for
use by this jacow tool in comparing crucial information between uploaded
documents and the csv file.

Currently, I manually download the spms file and add it to the git repo, then update docker.


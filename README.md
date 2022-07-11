[![Build Status](https://travis-ci.com/AustralianSynchrotron/jacow-validator.svg?branch=master)](https://travis-ci.com/AustralianSynchrotron/jacow-validator)

[![codecov](https://codecov.io/gh/AustralianSynchrotron/jacow-validator/branch/master/graph/badge.svg)](https://codecov.io/gh/AustralianSynchrotron/jacow-validator/)

# jacow_validator
Scripts to validate JACoW docx proceedings against the official template.

## Setup using AustralianSynchrotron jacow-validator

    git clone git@github.com:AustralianSynchrotron/jacow-validator.git
    pip install -r requirments.txt
    cd jacow-validator

Each conference has a url

grab a copy of it and save it to your computer

Add a conference if you are admin:
e.g.
Short Name: IPAC19
url: https://spms.kek.jp/pls/ipac19/references.csv
path: References_ibic20.csv


Where for each conference, **url** is set to the currently applicable url
and **path** is set to the location on your filesystem
where you saved the file.

##  Setup using forked jacow-validator

1. Fork this project to your own github account

2. Clone your fork to your computer

3. Add the AustralianSynchrotron repo as one of your remote's called "upstream":

    `git remote add upstream https://github.com/AustralianSynchrotron/jacow-validator.git`

4. Ensure docker is installed:

## Running without docker

(for development mode create a .env file with FLASK_ENV=development)

    pipenv run app

open http://localhost:5000/

### Running with docker on Windows

1. Make sure docker is running on your computer

2. Open a command prompt

3. Browse to the jacow-validator folder
4. create an .env file with variables where password is whatever you want

POSTGRES_USER=jacowuser
POSTGRES_PASSWORD=<password>
POSTGRES_DB=jacow

5. Type docker-compose up --build

6. For the first time use, you will need to
   * browse to /register and create an account
   * exec into the docker container with the database
   * docker exec -it <container> /bin/bash
   * login to postgres with the credentials in your .env
   * psql -U jacowuser
   * update the user in the app_user table with is_admin, is_editor and is_active set to true.
   * \c jacow
   * browse to /login page
   * login as new user
   * then you can use the interface to add conferences


### Running in PyCharm

*These steps work for pycharm's community edition which doesn't feature native flask support.*

1. Open pycharm and open the project

2. **File** > **Settings** > *this project* > **project interpreter**

    a. Set the interpreter to use pipenv

3. **Run** > **Edit Configurations** > Add new configuration (`+` button) > Choose Python

    1. Name it jacow-validator or similar

    1. Set the script path to point to the flask that is used by your pipenv virtual environment

        1. You can find the location of your virtual environment's files using the command `pipenv --venv` ran from within your project directory

        1. Your flask script will be located within a **bin** folder at that location so if `pipenv --venv` outputs:

            /home/*user*/.local/share/virtualenvs/jacow-validator-Awl2i6Az/

            then you will need to enter into the script path field:

            /home/*user*/.local/share/virtualenvs/jacow-validator-Awl2i6Az/bin/flask

    1. In the parameters type `run`

    1. Add a new environment variable called **FLASK_APP** and set it to the path to the `wsgi.py` file in the project root:

        example: FLASK_APP=/home/*user*/apps/jacow-validator/wsgi.py

4. Hitting the (play) or (debug) buttons in pycharm should now work to launch the app which you should now be able to see at http://localhost:5000/

## Testing

    pipenv run tox

## Testing in pycharm

1. Locate the tox.ini file in your file explorer

2. Right click tox.ini and select `run 'Tox'`

3. Note that you may have to reselect your flask run configuration afterwards
    in the top right of the IDE.

## Deployment

In the interests of keeping this readme clean and relevant to local
development, the details of where and how this project was deployed can
be found in the [deployment readme](./DEPLOYMENT.md)


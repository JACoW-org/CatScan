FROM python:3.9.5

ARG BUILD_GIT_BRANCH
ARG BUILD_GIT_COMMIT
ARG BUILD_GIT_AUTHOR
ARG BUILD_GIT_AUTHOR_NAME
ARG BUILD_GIT_REPO_LINK
ARG BUILD_CREATED
ARG BUILD_NUMBER

# add user csbs
RUN useradd -ms /bin/bash jacow

RUN mkdir -p /var/tmp
WORKDIR /home/jacow

COPY requirements.txt ./
RUN pip install -r requirements.txt

#RUN pip install pipenv
#COPY Pipfile* ./
#COPY setup.py ./
#RUN pipenv lock --requirements > requirements.txt
COPY .flaskenv boot.sh ./
COPY setup.py README.md ./
COPY src src

RUN pip install -e .

COPY migrations migrations
COPY spms spms
COPY wsgi.py ./

# uses the setup file to install the app to be able to run commandline commands defined in it.
#RUN pip install -e .

# Store all build args env variables into a file for later use
RUN env | grep BUILD_ > build_envs.txt; exit 0

RUN chmod +x boot.sh

RUN chown -R jacow:jacow ./
RUN chown -R jacow:jacow /var/tmp
USER jacow

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]

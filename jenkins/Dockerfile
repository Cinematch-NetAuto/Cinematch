# Jenkins with Python added, so the pipeline can lint and test the backend.
#
# The official Jenkins image has Java and Git but no Python. This adds
# python3 and venv; the Jenkinsfile installs the backend's packages into a
# venv inside the build, from backend/requirements.txt.
#
#   docker compose up -d jenkins     build it (first time) and start it
#   http://localhost:8081            the Jenkins web page

FROM jenkins/jenkins:2.580.1-lts-jdk21

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*
USER jenkins

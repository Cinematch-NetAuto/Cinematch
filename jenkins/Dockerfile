# Jenkins with Python and Node.js added, so the pipeline can check the backend
# and build the frontend.
#
# The official Jenkins image has Java and Git only. This adds python3 and venv
# (the Jenkinsfile installs the backend's packages into a venv, from
# backend/requirements.txt) and Debian's nodejs and npm (Node.js 20.19, the
# oldest version Vite 8 accepts; npm ci installs from frontend/package-lock.json).
#
#   docker compose up -d jenkins     build it (first time) and start it
#   docker compose build jenkins     rebuild it after this file changes
#   http://localhost:8081            the Jenkins web page

FROM jenkins/jenkins:2.580.1-lts-jdk21

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv nodejs npm \
    && rm -rf /var/lib/apt/lists/*
USER jenkins

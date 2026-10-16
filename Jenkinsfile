// CineMatch pipeline. Jenkins reads this file from the repository and runs it
// for every new commit on every branch (a Multibranch Pipeline job that checks
// GitHub every 5 minutes).
//
// Stages run in order: install -> lint -> test. A red stage stops the build.
// Secrets never go in this file; they live in Manage Jenkins -> Credentials.
// The frontend build stage is added in step 39.

pipeline {
    agent any

    options {
        timeout(time: 15, unit: 'MINUTES')  // a stuck build fails instead of hanging
        disableConcurrentBuilds()           // one build at a time per branch
    }

    stages {
        stage('Backend: install') {
            steps {
                dir('backend') {
                    sh 'python3 -m venv .venv'
                    sh '.venv/bin/pip install --quiet --disable-pip-version-check -r requirements.txt'
                }
            }
        }
        stage('Backend: lint') {
            steps {
                dir('backend') {
                    sh '.venv/bin/ruff check .'
                }
            }
        }
        stage('Backend: test') {
            steps {
                dir('backend') {
                    sh '.venv/bin/pytest --cov=app --junitxml=junit.xml'
                }
            }
        }
    }

    post {
        always {
            // Jenkins reads this file to draw its "Test Result" page.
            junit testResults: 'backend/junit.xml', allowEmptyResults: true
        }
        failure {
            echo 'Build failed: open the red stage above and read its log.'
        }
    }
}

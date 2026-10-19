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

    environment {
        // Jenkins and the database share the Docker network from docker-compose.yml,
        // so the database host is "db". The tests use "<name>_test", here
        // cinematch_ci_0_test or cinematch_ci_1_test: never a laptop's database.
        // One per executor (build slot): two builds can run at once, for example
        // dev and a feature branch after a merge, and the tests empty every table
        // before each test. A shared database let each run delete the other's users.
        // The user and password are the public development defaults, not a secret.
        DATABASE_URL = "postgresql+psycopg://cinematch:cinematch@db:5432/cinematch_ci_${env.EXECUTOR_NUMBER}"
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

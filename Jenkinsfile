pipeline {
  agent any
  stages {
    stage('starting') {
      steps {
        echo 'Starting Deployment'
      }
    }

    stage('check git') {
      steps {
        git(url: 'https://github.com/Callus4815/charles-web', branch: 'master', changelog: true, poll: true)
        git(url: 'https://github.com/Callus4815/charles-web', branch: 'heroku', changelog: true, poll: true)
      }
    }

  }
}
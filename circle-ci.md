# Create a circle.yml file for your repo

This document outlines how to create a circle.yml file to configure CircleCI to work with herd-service. circle.yml is a simple YAML file where you make any configurations necessary for your web app/service. You place the file in your git repo's root directory and CircleCI reads the file each time it runs a build.

For a full explanation of configuring CircleCI, please review [their documentation](https://circleci.com/docs/configuration).

## machine

### services

Identify the service you are using:

`- docker`

### environment

Add non-secret environment vars for herd & Google Cloud. Secret environment variables (credentials) are entered in the CCI UI (see [below](https://github.com/OAODEV/herd-service/wiki/Setup-Circle-CI-for-use-with-herd-service#environmental-variables)).

    herd_service_name: foo-service

    herd_unittest_cmd: python -m unittest discover # test command

    herd_build_tag: $(cat $CIRCLE_PROJECT_REPONAME/Version)_build.$(echo $CIRCLE_SHA1 | cut -c1-7)

    gcloud_project_id: lexical-cider-93918 # the google cloud project id

    CLOUDSDK_CORE_DISABLE_PROMPTS: 1
    CLOUDSDK_PYTHON_SITEPACKAGES: 1
    CLOUDSDK_COMPUTE_ZONE: us-central1-b
    PATH: $PATH:/home/ubuntu/google-cloud-sdk/bin

## dependencies

### cache_directories

Specify directories for the  cache you’ll make later: 

    - ~/google-cloud-sdk
    - ~/docker

### override

Install gcloud by adding the following:

    - if [ ! -d ~/google-cloud-sdk ]; then curl https://sdk.cloud.google.com | bash; fi
    - ~/google-cloud-sdk/bin/gcloud components update

 Notify  the herd service about the new commit:

    - curl --header X-CI-Token:$ci_token http://104.197.109.161/commit/$CIRCLE_PROJECT_REPONAME/$CIRCLE_BRANCH/$CIRCLE_BRANCH/$CIRCLE_SHA

Build the image for gcr.io by adding the following:

## build the image

    - echo $gcloud_key | base64 --decode > gcloud.json; gcloud auth activate-service-account $gcloud_email --key-file gcloud.json; ssh-keygen -f ~/.ssh/google_compute_engine -N ""
    - if [[ -e ~/docker/image.tar ]]; then docker load -i ~/docker/image.tar; fi
    - gcloud docker -a
    - docker build -t us.gcr.io/$gcloud_project_id/$herd_service_name:$herd_build_tag .

Cache the image to speed up the next build:

    - mkdir -p ~/docker; docker save us.gcr.io/$gcloud_project_id/$herd_service_name:$herd_build_tag > ~/docker/image.tar

## test

### override

Use the gcr.io image to execute unit tests by adding the following. 

    - docker run us.gcr.io/$gcloud_project_id/$herd_service_name:$herd_build_tag $herd_unittest_cmd

## deployment

### index

We are only deploying one environment, so we name it index

#### branch

Match the branch names and execute the commands where the name matches.

    /.*/

#### commands

Deploy the image to gcr.io by adding the following.

    - gcloud docker push us.gcr.io/$gcloud_project_id/$herd_service_name:$herd_build_tag

Notify  the herd service about the new build:

    - curl --header X-CI-Token:$ci_token http://104.197.109.161/build/$CIRCLE_SHA1/us.gcr.io/lexical-cider-93918/$herd_service_name:$herd_build_tag

## Full example

    machine:
      services:
        - docker
      environment:
        herd_service_name: foo-service # your service name
        herd_unittest_cmd: python -m unittest discover # your test command

        herd_build_tag: $(cat $CIRCLE_PROJECT_REPONAME/Version)_build.$(echo $CIRCLE_SHA1 | cut -c1-7)

        gcloud_project_id: lexical-cider-93918 # the google cloud project id

        CLOUDSDK_CORE_DISABLE_PROMPTS: 1
        CLOUDSDK_PYTHON_SITEPACKAGES: 1
        CLOUDSDK_COMPUTE_ZONE: us-central1-b
        PATH: $PATH:/home/ubuntu/google-cloud-sdk/bin

    dependencies:
      cache_directories:
        - ~/google-cloud-sdk
        - ~/docker
      override:
        # install gcloud
        - if [ ! -d ~/google-cloud-sdk ]; then curl https://sdk.cloud.google.com | bash; fi
        - ~/google-cloud-sdk/bin/gcloud components update

        - curl --header X-CI-Token:$ci_token http://104.197.109.161/commit/$CIRCLE_PROJECT_REPONAME/$CIRCLE_BRANCH/$CIRCLE_BRANCH/$CIRCLE_SHA1

        # build the image
        - echo $gcloud_key | base64 --decode > gcloud.json; gcloud auth activate-service-account $gcloud_email --key-file gcloud.json; ssh-keygen -f ~/.ssh/google_compute_engine -N ""
        - if [[ -e ~/docker/image.tar ]]; then docker load -i ~/docker/image.tar; fi
        - gcloud docker -a
        - docker build -t us.gcr.io/$gcloud_project_id/$herd_service_name:$herd_build_tag .

        # cache the image to speed up the next build
        - mkdir -p ~/docker; docker save us.gcr.io/$gcloud_project_id/$herd_service_name:$herd_build_tag > ~/docker/image.tar

    test:
      override:
        - docker run us.gcr.io/$gcloud_project_id/$herd_service_name:$herd_build_tag $herd_unittest_cmd

    deployment:
      index:
        branch: /.*/
        commands:
          - gcloud docker push us.gcr.io/$gcloud_project_id/$herd_service_name:$herd_build_tag
          - curl --header X-CI-Token:$ci_token http://104.197.109.161/build/$CIRCLE_SHA1/us.gcr.io/$gcloud_project_id/$herd_service_name:$herd_build_tag


# Add your project to Circle CI

Go to [https://circleci.com/add-projects](https://circleci.com/add-projects) and follow the instructions to choose which GitHub project to watch. Expect CCI builds to fail until all procedures outlined in this document are implemented.

# Environmental Variables

Since your circle.yml file lives in the git repo, you will want to enter all sensitive/secret values as environmental variables in the CCI UI so they are not exposed on GitHub,etc. 

On the Project Settings page for your repo, click Tweaks > Environmental Variables in the left hand sidebar. To obtain an existing set of values for OAO Technology, use the following:

<table>
  <tr>
    <td>Name</td>
    <td>Location of value</td>
  </tr>
  <tr>
    <td>ci_token</td>
    <td>"CI token for herd service" entry in adops.1password.com Technology Vault.</td>
  </tr>
  <tr>
    <td>gcloud_email</td>
    <td>"gcloud credentials" secure note in adops.1password.com Technology Vault.</td>
  </tr>
  <tr>
    <td>gcloud_key</td>
    <td>"gcloud credentials" secure note in adops.1password.com Technology Vault.</td>
  </tr>
</table>


If you need to create new values for the above (thereby invalidating any existing ones):

* First generate a new JSON key in the [Developer Console](https://console.developers.google.com/):

    * Select API Manager from the Gallery (hamburger to the left of "Google Developers Console")

    * Select Credentials

    * Select (or create) your service account.

    * Click "Generate new JSON key"

* Base64 encode the JSON file

    * cat keyfile.json | base64

* Set `gcloud_key` the resulting block of base64 encoded text.

* Set `gcloud_email` to the email address listed under "Service Account" on the page for same the OAuth 2.0 client ID you selected/created in API Manager > Credentials page.

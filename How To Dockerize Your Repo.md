# What is a Docker container?

From the [Docker website](https://www.docker.com/what-docker):

> Docker containers wrap up a piece of software in a complete filesystem that contains everything it needs to run: code, runtime, system tools, system libraries – anything you can install on a server. This guarantees that it will always run the same, regardless of the environment it is running in.

Containers allow you to run your application as a service and help reduce concerns about inconsistencies between development and production environments. It enables you to design the entire cycle of application development, testing and distribution. To learn more about Docker, visit [their website](https://www.docker.com/).

Designing applications for containers keeps your code modular and helps to reduce the "it works on my machine!" problems. However, getting your code into a state that is containerize-able requires a few steps that are outlined below.

# Implement secret and sensitive information as configurable values

Your application may include sensitive or secret information (such as API keys or other credentials) as well as values that may need to be different depending on the environment. For example, database connection details for a development environment would be different than a production environment.

There are several ways to handle configurable values:

* Implemented as environment variables

    * [You can use docker run commands or other methods to set these at runtime](https://github.com/OAODEV/herd-service/wiki/How-To-Dockerize-an-Application#run-your-container)

* Mounting a file in the container at a specified location where the file name matches your key and whose content equals the value

    * This is how [Kubernetes handles secrets](http://kubernetes.io/v1.1/docs/user-guide/secrets.html). 

* Mounting a single file with all your variable names and values listed as key=value.

However you implement these configurable values, you need to update your code to access these values as they are implemented. However you do it, you want to make sure you keep your secrets out of the repo for security reasons.

At OAO, we have created a python library called [config-finder](https://github.com/OAODEV/config-finder) which can be installed via pip and implemented in a python project. More information on using that can be found in the [README for config-finder](https://github.com/OAODEV/config-finder/blob/master/README.md).

# Send log entries to STDOUT/STDERR

Docker logs capture all output sent to STDOUT and STDERR, so you’ll want to update your application to leverage this.  Executing docker logs will allow you to examine this output without having to actually enter the container. For more information on Docker logs, view [the reference page on Docker’s website](https://docs.docker.com/engine/reference/commandline/logs/).

To update your Python to log to STDOUT or STDERR, use the [logging.StreamHandler](https://docs.python.org/3.5/library/logging.handlers.html#streamhandler).

To update your JavaScript to log to STDOUT or STDERR, use `console.log()` or `console.error()` … or `process.stdout.write()` or `process.stderr.write()`, respectively.

# Create a Dockerfile

The Dockerfile is a text document that contains all the commands a user could call on the command line to assemble an image. 

Below is an explanation of some of the basic commands that should be included in a basic Dockerfile. For a full reference, please review the [Docker documentation](https://docs.docker.com/engine/reference/builder/#dockerfile-reference).

## FROM

The [FROM](https://docs.docker.com/engine/reference/builder/#from) instruction sets the Base Image for subsequent instructions. As such, a valid Dockerfile must have FROM as its first instruction. The image can be any valid image - whether it’s a public image like ubuntu … or one from a private repo (although that will require authentication). 

Example: `FROM us.gcr.io/lexical-cider-93918/generic-api:_build.6d5d817`

## MAINTAINER

[MAINTAINER](https://docs.docker.com/engine/reference/builder/#maintainer) sets the Author field of your image … and lets people know who to contact for more information about this container image.

Example: `MAINTAINER matt.urban@adops.com`

## RUN

The [RUN](https://docs.docker.com/engine/reference/builder/#run) instruction will execute any commands in a new layer on top of the current image and commit the results. The resulting committed image will be used for the next step in the Dockerfile. This makes it a good place to install any prerequisites that the application will expect to be installed in the environment that aren’t included in the base image used in FROM.

Example: `RUN apt-get update && apt-get install -y python-psycopg2`

## ADD

The [ADD](https://docs.docker.com/engine/reference/builder/#add) instruction copies new files, directories or remote file URLs from source identified in the first argument and adds them to the filesystem of the container at the path specified in the second argument. Multiple sources resource may be specified but if they are files or directories then they must be relative to the source directory that is being built (the context of the build).

Example: ADD service service

## CMD

The main purpose of a [CMD](https://docs.docker.com/engine/reference/builder/#cmd) is to provide defaults for an executing container. There can only be one CMD instruction in a Dockerfile. If you list more than one CMD then only the last CMD will take effect.

Example: `CMD python main.py`

# Build your container

Executing docker build builds Docker images from a Dockerfile and a "context". A build’s context is the files located in the specified path or GitHub url. For instance:

* `docker build .` 

    * creates an image from the current directory

* `docker build https://github.com/docker/rootfs.git#container:docker`

    * creates an image using a directory called docker in the branch container

Several options may be set on the command as well. For a full explanation, [please review the Docker reference](https://docs.docker.com/engine/reference/commandline/build/).

The successful execution of docker build will output the name of the image as:

`Successfully built [image name]`

# Run your container

The docker run command first creates a writeable container layer over the specified image, and then starts it using the specified command in your Dockerfile.

`docker run [image name]`

Several options may be set on the command as well. For a full explanation, [please review the Docker reference](https://docs.docker.com/engine/reference/commandline/run/).

One option that will be particularly convenient use of options are setting environment variables. This is particularly useful for setting a configuration when testing locally (at OAO, we are using [herd-service](https://github.com/OAODEV/herd-service) to set our configurations when pushed to an environment).

You can set environment variables individually by using the -e or --env flags on the command line. You can also use --env-file to read in a file of of environmental variables. Full details are available [here on Docker’s site](https://docs.docker.com/engine/reference/commandline/run/#set-environment-variables-e-env-env-file).


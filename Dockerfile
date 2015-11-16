FROM r.iadops.com/bottlebase:2
MAINTAINER jesse.miller@adops.com

# set up for configurability
RUN mkdir /secret

# create a working directory
RUN mkdir /herd
WORKDIR /herd

# add the api
ADD service /herd/service

CMD python3 -u service

from r.iadops.com/bottlebase:1

# set up for configurability
RUN mkdir /secret

# create a working directory
RUN mkdir /herd
WORKDIR /herd

# add the api
ADD service /herd/service

CMD python3 -u service

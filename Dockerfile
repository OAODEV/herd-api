FROM us.gcr.io/lexical-cider-93918/basebottle:_build.0273acb
MAINTAINER jesse.miller@adops.com

# get swagger client
RUN pip install requests

# set up for configurability
RUN mkdir /secret

# create a working directory
RUN mkdir /herd
WORKDIR /herd

# add the api
ADD service /herd/service

CMD python3 -u service

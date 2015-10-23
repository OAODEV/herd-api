FROM alpine:latest
MAINTAINER jesse.miller@adops.com

# install deps
RUN apk update && \
    apk add --update \
      build-base \
      postgresql \
      postgresql-dev \
      python3 \
      python3-dev
RUN pip3 install --upgrade pip && \
    pip3 install bottle \
                 psycopg2


# clean up from instalation
RUN rm -rf ~/.pip/cache/*
RUN apk del postgresql-dev \
            python3-dev \
    && rm -rf /var/cache/apk/* \
    && rm -rf /var/lib/postgresql/data

# set up for configurability
RUN mkdir /secret

# create a working directory
RUN mkdir /herd-api
WORKDIR /herd-api

# add the api
ADD service /herd-api/service
ADD tests /hserd-api/tests

CMD python3 service

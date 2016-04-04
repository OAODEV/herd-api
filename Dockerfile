FROM us.gcr.io/lexical-cider-93918/basebottle:_build.0273acb
MAINTAINER jesse.miller@adops.com

RUN echo "@edge http://nl.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories \
 && apk update \
 && apk add --update \
        postgresql@edge>=9.5 \
        postgresql-contrib@edge>=9.5 \
 && rm -rf /var/cache/apk/*

RUN pip install \
        hypothesis \
        nose \
        requests \
        testing.postgresql

# set up for configurability
RUN mkdir /secret

# create a working directory
RUN mkdir /herd
WORKDIR /herd

# make the postgres user own everything (so it can run the tests)
RUN chown -R postgres /herd

# add the api
ADD service /herd/service

CMD python3 -u service

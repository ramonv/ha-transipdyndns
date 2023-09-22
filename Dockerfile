ARG BUILD_FROM
FROM $BUILD_FROM

# Install requirements for add-on
RUN \
  apk add --no-cache \
    python3 py3-pip
RUN pip install transip_dns

COPY run.sh /
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]

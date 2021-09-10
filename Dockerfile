FROM ubuntu:18.04
ARG YANG_ID
ARG YANG_GID
ARG YANGCATALOG_CONFIG_PATH

ENV YANG_ID "$YANG_ID"
ENV YANG_GID "$YANG_GID"
ENV YANGCATALOG_CONFIG_PATH "$YANGCATALOG_CONFIG_PATH"
ENV confd_version 7.5

RUN apt-get -y update \
  && apt-get install -y build-essential clang cmake git gnupg2 gunicorn libpcre2-dev \
  libssl1.0.0 libssl-dev libxml2-dev openssh-client python3.6 python3-pip rsyslog systemd wget
RUN mkdir /home/w3cgrep
RUN cd /home; git clone https://github.com/CESNET/libyang.git \
  && cd /home/libyang; mkdir build \
  && cd /home/libyang/build \
  && cmake .. \
  && make \
  && make install

RUN rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip
RUN pip3 install requests
RUN pip3 install xym
COPY ./bottle-yang-extractor-validator/requirements.txt .
RUN pip3 install -r requirements.txt

RUN groupadd web
RUN useradd -d /home/bottle -m bottle

RUN mkdir /home/bottle/confd-${confd_version}
COPY ./resources/confd-${confd_version}.linux.x86_64.installer.bin /home/bottle/bottle-yang-extractor-validator/confd-${confd_version}.linux.x86_64.installer.bin
COPY ./resources/yumapro-client-20.10-9.u1804.amd64.deb /home/bottle/bottle-yang-extractor-validator/yumapro-client-20.10-9.u1804.amd64.deb
RUN /home/bottle/bottle-yang-extractor-validator/confd-${confd_version}.linux.x86_64.installer.bin /home/bottle/confd-${confd_version}

RUN dpkg -i /home/bottle/bottle-yang-extractor-validator/yumapro-client-20.10-9.u1804.amd64.deb

RUN mkdir /var/run/yang
RUN chown -R ${YANG_ID}:${YANG_GID} /var/run/yang

COPY ./bottle-yang-extractor-validator/ /home/bottle/bottle-yang-extractor-validator/

ENV VIRTUAL_ENV=/home/bottle/bottle-yang-extractor-validator

WORKDIR /home/bottle/bottle-yang-extractor-validator

EXPOSE 8090
# Support arbitrary UIDs as per OpenShift guidelines

CMD chown -R ${YANG_ID}:${YANG_GID} /var/run/yang && service rsyslog start && gunicorn yangvalidator.wsgi:application -c gunicorn.conf.py

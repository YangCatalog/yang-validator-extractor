FROM ubuntu:18.04
ARG YANG_ID
ARG YANG_GID
ARG YANGCATALOG_CONFIG_PATH
ARG CONFD_VERSION

ENV YANG_ID "$YANG_ID"
ENV YANG_GID "$YANG_GID"
ENV YANGCATALOG_CONFIG_PATH "$YANGCATALOG_CONFIG_PATH"
ENV CONFD_VERSION "$CONFD_VERSION"

RUN apt-get -y update
RUN apt-get install -y build-essential clang cmake git gnupg2 gunicorn libpcre2-dev \
  libssl1.0.0 libssl-dev libxml2-dev openssh-client python3.6 python3-pip rsyslog systemd wget
RUN mkdir /home/w3cgrep
WORKDIR /home
RUN git clone https://github.com/CESNET/libyang.git
RUN mkdir -p /home/libyang/build
WORKDIR /home/libyang/build
RUN cmake -D CMAKE_BUILD_TYPE:String="Release" .. && make && make install

RUN rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip
RUN pip3 install requests
RUN pip3 install xym
COPY ./yang-validator-extractor/requirements.txt .
RUN pip3 install -r requirements.txt

RUN groupadd web
RUN useradd -d /home/yangvalidator -m yangvalidator

RUN mkdir /home/yangvalidator/confd-${CONFD_VERSION}
COPY ./resources/confd-${CONFD_VERSION}.linux.x86_64.installer.bin /home/yangvalidator/yang-extractor-validator/confd-${CONFD_VERSION}.linux.x86_64.installer.bin
COPY ./resources/yumapro-client-20.10-9.u1804.amd64.deb /home/yangvalidator/yang-extractor-validator/yumapro-client-20.10-9.u1804.amd64.deb
RUN /home/yangvalidator/yang-extractor-validator/confd-${CONFD_VERSION}.linux.x86_64.installer.bin /home/yangvalidator/confd-${CONFD_VERSION}

RUN dpkg -i /home/yangvalidator/yang-extractor-validator/yumapro-client-20.10-9.u1804.amd64.deb

RUN mkdir /var/run/yang
RUN chown -R ${YANG_ID}:${YANG_GID} /var/run/yang

COPY ./yang-validator-extractor/ /home/yangvalidator/yang-extractor-validator/

ENV VIRTUAL_ENV=/home/yangvalidator/yang-extractor-validator

WORKDIR /home/yangvalidator/yang-extractor-validator

EXPOSE 8090
# Support arbitrary UIDs as per OpenShift guidelines

CMD chown -R ${YANG_ID}:${YANG_GID} /var/run/yang && service rsyslog start && gunicorn yangvalidator.wsgi:application -c gunicorn.conf.py

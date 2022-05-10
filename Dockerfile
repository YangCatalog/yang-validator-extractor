FROM ubuntu:18.04
ARG YANG_ID
ARG YANG_GID
ARG YANGCATALOG_CONFIG_PATH
ARG CONFD_VERSION
ARG YANGLINT_VERSION

ENV YANG_ID "$YANG_ID"
ENV YANG_GID "$YANG_GID"
ENV YANGCATALOG_CONFIG_PATH "$YANGCATALOG_CONFIG_PATH"
ENV CONFD_VERSION "$CONFD_VERSION"
ENV YANGLINT_VERSION "$YANGLINT_VERSION"

ENV VIRTUAL_ENV=/home/yangvalidator/yang-extractor-validator

RUN apt-get -y update
RUN apt-get install -y build-essential clang cmake git gnupg2 gunicorn libpcre2-dev \
  libssl1.0.0 libssl-dev libxml2-dev openssh-client python3.6 python3-pip rsyslog systemd wget curl

# Create 'yang' user and group
RUN groupadd -g ${YANG_GID} -r yang && useradd --no-log-init -r -g yang -u ${YANG_ID} -d /home yang

WORKDIR /home
RUN git clone -b ${YANGLINT_VERSION} --single-branch --depth 1 https://github.com/CESNET/libyang.git
RUN mkdir -p /home/libyang/build
WORKDIR /home/libyang/build
RUN cmake -D CMAKE_BUILD_TYPE:String="Release" .. && make && make install

RUN sed -i "/imklog/s/^/#/" /etc/rsyslog.conf
RUN rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip
COPY ./yang-validator-extractor/requirements.txt .
RUN pip3 install -r requirements.txt
# TODO: remove next step from build when depend.py will be fixed in next pyang release
# https://github.com/mbj4668/pyang/pull/793
COPY ./yang-validator-extractor/pyang_plugin/depend.py /usr/lib/python3.6/site-packages/pyang/plugins/.

RUN mkdir -p /home/yangvalidator/confd-${CONFD_VERSION}
COPY ./resources/confd-${CONFD_VERSION}.linux.x86_64.installer.bin $VIRTUAL_ENV/confd-${CONFD_VERSION}.linux.x86_64.installer.bin
COPY ./resources/yumapro-client-20.10-9.u1804.amd64.deb $VIRTUAL_ENV/yumapro-client-20.10-9.u1804.amd64.deb
RUN $VIRTUAL_ENV/confd-${CONFD_VERSION}.linux.x86_64.installer.bin /home/yangvalidator/confd-${CONFD_VERSION}

WORKDIR $VIRTUAL_ENV
RUN dpkg -i $VIRTUAL_ENV/yumapro-client-20.10-9.u1804.amd64.deb
COPY ./yang-validator-extractor/ $VIRTUAL_ENV/
RUN chown -R ${YANG_ID}:${YANG_GID} /home
RUN mkdir /var/run/yang

EXPOSE 8090
# Support arbitrary UIDs as per OpenShift guidelines

CMD chown -R ${YANG_ID}:${YANG_GID} /var/run/yang && service rsyslog start && gunicorn yangvalidator.wsgi:application -c gunicorn.conf.py

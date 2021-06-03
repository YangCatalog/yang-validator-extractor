FROM ubuntu:18.04
ARG YANG_ID
ARG YANG_GID

ENV YANG_ID "$YANG_ID"
ENV YANG_GID "$YANG_GID"

RUN apt-get -y update
RUN apt-get -y install rsync python3.6 python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install requests
RUN pip3 install xym

COPY ./bottle-yang-extractor-validator/sync.sh .
RUN ./sync.sh


FROM ubuntu:18.04
ENV confd_version 7.5

RUN apt-get -y update
RUN apt-get install -y \
    wget \
    gnupg2

RUN apt-get -y update \
  && apt-get -y install clang cmake libpcre2-dev git libxml2-dev rsyslog systemd \
  && cd /home; mkdir w3cgrep \
  && cd /home; git clone https://github.com/CESNET/libyang.git \
  && cd /home/libyang; mkdir build \
  && cd /home/libyang/build && cmake .. && make && make install

# Install Java.
RUN \
  apt-get -y update && \
  apt-get -y install openssh-client build-essential libssl-dev libssl1.0.0

RUN apt-get -y update

RUN apt-get -y install \
	python3.6 \
	python3-pip \
    openssh-client gunicorn \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip
RUN pip3 install requests
RUN pip3 install xym
COPY ./bottle-yang-extractor-validator/requirements.txt .
RUN pip3 install -r requirements.txt

RUN groupadd web
RUN useradd -d /home/bottle -m bottle

COPY ./bottle-yang-extractor-validator/* /home/bottle/bottle-yang-extractor-validator/

ENV VIRTUAL_ENV=/home/bottle/bottle-yang-extractor-validator

WORKDIR /home/bottle

RUN mkdir /home/bottle/confd-${confd_version}
COPY ./resources/confd-${confd_version}.linux.x86_64.installer.bin /home/bottle/bottle-yang-extractor-validator/confd-${confd_version}.linux.x86_64.installer.bin
COPY ./resources/yumapro-client-20.10-6.u1804.amd64.deb home/bottle/bottle-yang-extractor-validator/yumapro-client-20.10-6.u1804.amd64.deb
RUN /home/bottle/bottle-yang-extractor-validator/confd-${confd_version}.linux.x86_64.installer.bin /home/bottle/confd-${confd_version}

RUN dpkg -i home/bottle/bottle-yang-extractor-validator/yumapro-client-20.10-6.u1804.amd64.deb

RUN mkdir /var/run/yang
RUN chown -R ${YANG_ID}:${YANG_GID} /var/run/yang

RUN mkdir -pv /var/tmp/yangmodules/extracted
COPY --from=0 /var/tmp/yangmodules/extracted /var/tmp/yangmodules/extracted

WORKDIR /home/bottle/bottle-yang-extractor-validator

EXPOSE 8090
# Support arbitrary UIDs as per OpenShift guidelines

CMD chown -R ${YANG_ID}:${YANG_GID} /var/run/yang && service rsyslog start && gunicorn yangvalidator.wsgi:application -c gunicorn.conf.py

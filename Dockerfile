FROM ubuntu:18.04
ARG YANG_ID
ARG YANG_GID

ENV YANG_ID "$YANG_ID"
ENV YANG_GID "$YANG_GID"

RUN apt-get update
RUN apt-get -y install rsync python3.6 python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install requests
RUN pip3 install xym

COPY ./bottle-yang-extractor-validator/sync.sh .
RUN ./sync.sh


FROM ubuntu:18.04
ENV confd_version 7.3.1

RUN apt-get update
RUN apt-get install -y \
    wget \
    gnupg2

RUN apt-get update \
  && apt-get -y install clang cmake libpcre3-dev git libxml2-dev \
  && cd /home; mkdir w3cgrep \
  && cd /home; git clone https://github.com/CESNET/libyang.git \
  && cd /home/libyang; mkdir build \
  && cd /home/libyang/build && cmake .. && make && make install

# Install Java.
RUN \
  apt-get update && \
  apt-get install -y openssh-client build-essential libssl-dev libssl1.0.0

RUN apt-get update

RUN apt-get install -y \
	python3.6 \
	python3-pip \
    openssh-client uwsgi uwsgi-plugin-python3 \
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
COPY ./resources/yumapro-client-19.10-12.u1804.amd64.deb home/bottle/bottle-yang-extractor-validator/yumapro-client-19.10-12.u1804.amd64.deb
RUN /home/bottle/bottle-yang-extractor-validator/confd-${confd_version}.linux.x86_64.installer.bin /home/bottle/confd-${confd_version}

COPY ./bottle-yang-extractor-validator/yangvalidator.ini-dist $VIRTUAL_ENV/yangvalidator.ini

RUN dpkg -i home/bottle/bottle-yang-extractor-validator/yumapro-client-19.10-12.u1804.amd64.deb

RUN mkdir /var/run/yang
RUN chown -R ${YANG_ID}:${YANG_GID} /var/run/yang

RUN mkdir -pv /var/tmp/yangmodules/extracted
COPY --from=0 /var/tmp/yangmodules/extracted /var/tmp/yangmodules/extracted

WORKDIR /home/bottle/bottle-yang-extractor-validator

EXPOSE 8090
# Support arbitrary UIDs as per OpenShift guidelines

CMD chown -R ${YANG_ID}:${YANG_GID} /var/run/yang && uwsgi --ini yangvalidator.ini

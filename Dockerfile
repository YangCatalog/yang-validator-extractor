FROM ubuntu:latest

RUN apt-get update
RUN apt-get -y install rsync python-pip
RUN pip2 install --upgrade pip
RUN pip2 install requests
RUN pip2 install xym

COPY ./sync.sh .
RUN ./sync.sh


FROM ubuntu:latest
ENV confd_version 6.7

RUN apt-get update
RUN apt-get install -y \
    wget \
    gnupg2

RUN echo "deb http://download.opensuse.org/repositories/home:/liberouter/xUbuntu_18.04/ /" > /etc/apt/sources.list.d/libyang.list
RUN wget -nv https://download.opensuse.org/repositories/home:liberouter/xUbuntu_18.04/Release.key -O Release.key
RUN apt-key add - < Release.key

RUN apt-get update

RUN apt-get install -y \
	libyang \
	python-pip

RUN pip2 install --upgrade pip
RUN pip2 install \
	pyang \
    requests


RUN groupadd web
RUN useradd -d /home/bottle -m bottle

COPY . /home/bottle/

WORKDIR /home/bottle
RUN pip2 install .

RUN mkdir /home/bottle/confd-${confd_version}
RUN /home/bottle/confd-${confd_version}.linux.x86_64.installer.bin /home/bottle/confd-${confd_version}

RUN mkdir -pv /var/tmp/yangmodules/extracted 
COPY --from=0 /var/tmp/yangmodules/extracted /var/tmp/yangmodules/extracted 

WORKDIR /home/bottle/bottle-yang-extractor-validator

EXPOSE 8080

ENTRYPOINT /usr/bin/python /home/bottle/bottle-yang-extractor-validator/main.py --confd-install-path /home/bottle/confd-${confd_version}

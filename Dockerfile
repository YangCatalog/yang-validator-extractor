FROM ubuntu:latest

RUN apt-get update
RUN apt-get -y install rsync python-pip
RUN pip2 install --upgrade pip
RUN pip2 install xym

COPY ./sync.sh .
RUN ./sync.sh


FROM ubuntu:latest
ENV confd_version 6.5.3

RUN echo "deb http://download.opensuse.org/repositories/home:/liberouter/xUbuntu_17.04/ /" > /etc/apt/sources.list.d/libyang.list
RUN apt-get update
RUN apt-get install --allow-unauthenticated -y \
	libyang \
	python-pip

RUN pip2 install --upgrade pip
RUN pip2 install \
	pyang

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

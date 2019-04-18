FROM ubuntu:latest

RUN apt-get update
RUN apt-get -y install rsync python3.6 python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install requests
RUN pip3 install xym

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
	python3.6 \
	python3-pip \
    openssh-client

RUN pip3 install --upgrade pip
RUN pip3 install requests
RUN pip3 install xym
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt


RUN groupadd web
RUN useradd -d /home/bottle -m bottle

COPY ./* /home/bottle/bottle-yang-extractor-validator/

WORKDIR /home/bottle

RUN mkdir /home/bottle/confd-${confd_version}
RUN /home/bottle/bottle-yang-extractor-validator/confd-${confd_version}.linux.x86_64.installer.bin /home/bottle/confd-${confd_version}

RUN mkdir -pv /var/tmp/yangmodules/extracted 
COPY --from=0 /var/tmp/yangmodules/extracted /var/tmp/yangmodules/extracted 

WORKDIR /home/bottle/bottle-yang-extractor-validator

RUN ln -s /usr/bin/yanglint /usr/local/bin/yanglint
EXPOSE 8090
# Support arbitrary UIDs as per OpenShift guidelines
USER 1000:1001
CMD exec uwsgi --socket :8090 --protocol uwsgi --plugin python3 \
  -w yangvalidator.wsgi:application --need-app
FROM debian:8

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y sysvinit-core
RUN apt-get remove -y systemd
RUN apt-get install -y python python-pip
RUN pip install --upgrade pip && pip install future

CMD ["/bin/cat"]

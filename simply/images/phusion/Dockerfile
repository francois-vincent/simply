FROM jedisct1/phusion-baseimage-latest
# https://hub.docker.com/r/jedisct1/phusion-baseimage-latest/
RUN apt-get update && apt-get upgrade -y
# python3 is already installed
RUN apt-get install -y python python-pip python3-pip
RUN pip install --upgrade pip && pip install future
RUN pip3 install --upgrade pip

CMD ["/bin/cat"]

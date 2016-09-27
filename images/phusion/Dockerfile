FROM jedisct1/phusion-baseimage-latest
# https://hub.docker.com/r/jedisct1/phusion-baseimage-latest/
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y python python-pip
RUN pip install --upgrade pip

CMD ["/bin/cat"]

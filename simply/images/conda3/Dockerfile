FROM progrium/busybox
# https://github.com/elyase/docker
MAINTAINER Yaser Martinez Palenzuela
RUN opkg-install bash bzip2
ADD conda_install.sh /root/conda_install.sh
RUN ["bash", "/root/conda_install.sh"]
ENV PATH /root/miniconda3/bin:$PATH
RUN conda install pip

CMD ["/bin/cat"]

FROM progrium/busybox
MAINTAINER Yaser Martinez Palenzuela
RUN opkg-install bash bzip2 mysql-server libopenssl
ADD conda_install.sh /root/conda_install.sh
RUN ["bash", "/root/conda_install.sh"]
ENV PATH /root/miniconda2/bin:$PATH
CMD ["/bin/cat"]

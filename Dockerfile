# A Dockerfile for running the Open Modeling Framework
FROM ubuntu:18.04
MAINTAINER <david.pinney@nreca.coop>

# Install and setup OMF reqs
RUN apt-get -y update && apt-get install -y python3 sudo vim python3-pip python3-setuptools
RUN mkdir /home/omf
RUN mkdir /home/omf/omf

# Do the install and have it cached as an intermediate image.
COPY requirements.txt /home/omf/
COPY setup.py /home/omf/
COPY install.py /home/omf/
RUN cd /home/omf/; python3 install.py
#RUN cd /home/omf/; python3 setup.py develop

# Run the OMF
VOLUME ["/home/omf/omf/"]
WORKDIR /home/omf/omf/
ENTRYPOINT ["python3"]
CMD ["web.py"]

# INSTRUCTIONS
# ============
# - Navigate to this directory
# - Build image with command `docker build . -f Dockerfile -t omfim`
# - Run image in background with `docker run -d -p 5000:5000 -v "`pwd`/omf":/home/omf/omf/ --name omfcont omfim`
# - View at http://127.0.0.1:5000
# - Stop it with `docker stop omfcont` and remove it with `docker rm omfcont`.
# - Delete the images with `docker rmi omfim`
# - Note that the source is mounted via a volume, so changes in the local file system will be reflected in the image/container
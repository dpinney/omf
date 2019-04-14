# A Dockerfile for running the Open Modeling Framework
# Tested on 16 July 2018 with Docker Version 18.06.1-ce-mac73 (26764)
FROM ubuntu:16.04
MAINTAINER <david.pinney@nreca.coop>

# Install and setup OMF reqs
RUN apt-get -y update && apt-get install -y python sudo vim
RUN mkdir /home/omf
# Do the install and have it cached as an intermediate image.
COPY install.py /home/omf/
COPY requirements.txt /home/omf/
COPY setup.py /home/omf/
RUN cd /home/omf/; python install.py

# Run the OMF
VOLUME ["/home/omf/omf/"]
WORKDIR /home/omf/omf/
ENTRYPOINT ["python"]
CMD ["web.py"]

# INSTRUCTIONS
# ============
# - Navigate to this directory
# - Build image with command `docker build . -f dev.Dockerfile -t <IMAGE_NAME>`
# - Note that 
# - Run image in background with `docker run -d -p 5000:5000 -v "`pwd`/omf":/home/omf/omf/ --name omfdevc omfdev`
# - View at http://127.0.0.1:5000
# - Stop it with `docker stop <CONT_NAME>` and remove it with `docker rm <CONT_NAME>`.
# - Delete the images with `docker rmi <IMAGE_NAME>`
# 
# FEATURE IDEAS
# =============
# - Python "build" script to create, start and exit the image

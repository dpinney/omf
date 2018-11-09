# A Dockerfile for running the Open Modeling Framework
# Tested on 16 July 2018 with Docker Version 18.03.1-ce-mac65 (24312)
FROM ubuntu:16.04
MAINTAINER <david.pinney@nreca.coop>

# Install and setup OMF reqs
RUN apt-get -y update && apt-get install -y python sudo vim
RUN mkdir /home/omf
# TODO: just move install.py and run to setup environment then move the rest. Makes this more cacheable.
COPY . /home/omf/
RUN cd /home/omf/; python install.py

# Make sure the docker instance listens externally
RUN sed -i -e 's/host="127.0.0.1"/host="0.0.0.0"/g' /home/omf/omf/web.py

# Run the OMF
WORKDIR /home/omf/omf
ENTRYPOINT ["python"]
CMD ["web.py"]

# INSTRUCTIONS
# ============
# - Navigate to this directory
# - Build image with command `docker build . -t <IMAGE_NAME>`
# - Run image in background with `docker run -d -p 5000:5000 --name <CONT_NAME> <IMAGE_NAME>`
# - View at http://127.0.0.1:5000
# - Stop it with `docker stop <CONT_NAME>` and remove it with `docker rm <CONT_NAME>`.
# - Delete the images with `docker rmi <IMAGE_NAME>`
# 
# FEATURE IDEAS
# =============
# - Python "build" script to create, start and exit the image
# - Modify Dockerfile to use a network drive containing the omf repo instead of doing a fresh git pull
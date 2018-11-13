# A Dockerfile for running the Open Modeling Framework
# Tested on 2018-11-08 with Docker Version 18.06.1-ce-mac73 (26764)
FROM ubuntu:16.04
MAINTAINER <david.pinney@nreca.coop>

# Install and setup OMF reqs
RUN apt-get -y update && apt-get install -y python sudo vim
RUN mkdir /home/omf
# TODO: just move install.py and run to setup environment then move the rest. Makes this more cacheable.
COPY install.py /home/omf/
COPY requirements.txt /home/omf/
COPY setup.py /home/omf/
RUN cd /home/omf/; python install.py
# Put the rest of the source in there.
COPY omf /home/omf/omf

# Run the OMF
WORKDIR /home/omf/omf
ENTRYPOINT ["python"]
CMD ["grip.py"]

# INSTRUCTIONS
# ============
# - Navigate to this directory
# - Build image with command `docker build grip.Dockerfile -t <IMAGE_NAME>`
# - Run image in background with `docker run -d -p 5000:5000 --name <CONT_NAME> <IMAGE_NAME>`
# - View at http://127.0.0.1:5000
# - Stop it with `docker stop <CONT_NAME>` and remove it with `docker rm <CONT_NAME>`.
# - Delete the images with `docker rmi <IMAGE_NAME>`
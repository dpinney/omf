# A Dockerfile for running the Open Modeling Framework
# Tested on 19 April 2018 with Docker Version 18.03.0-ce-mac60 (23751)
FROM ubuntu:16.04
MAINTAINER <david.pinney@nreca.coop>

# Install and setup OMF reqs
RUN apt-get -y update && apt-get install -y git python sudo
RUN cd home; git clone --depth 1 https://github.com/dpinney/omf
RUN cd home/omf; python install.py

# Make sure the docker instance listens externally
RUN sed -i -e 's/host="127.0.0.1"/host="0.0.0.0"/g' /home/omf/omf/web.py

# Run the OMF
WORKDIR /home/omf/omf
ENTRYPOINT ["python"]
CMD ["web.py"]

# INSTRUCTIONS
# ============
# - Navigate to this directory
# - Build image with command `docker build . -t <chooseAnImageName>`
# - Run image in background with `docker run -d -p 5000:5000 --name <chooseContainerName> <imageNameFromAbove>`
# - View at http://127.0.0.1:5000
# - Stop it with `docker stop <containerNameFromAbove` and remove it with `docker rm <containerNameFromAbove>`.
# - Delete the images with `docker rmi <imageNameFromAbove>`
# 
# FEATURE IDEAS
# =============
# - Switch to install.py instead of manual apt commands
# - Python "build" script to create, start and exit the image
# - Modify Dockerfile to use a network drive containing the omf repo instead of doing a fresh git pull
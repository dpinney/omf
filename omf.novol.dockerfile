# A Dockerfile for running the Open Modeling Framework
FROM ubuntu:18.04

# Install and setup OMF reqs
RUN apt-get -y update && apt-get install -y git python3 sudo
RUN cd home; git clone --depth 1 https://github.com/dpinney/omf
RUN cd /home/omf; python3 install.py

# Run the OMF
EXPOSE 5000
WORKDIR /home/omf/omf
ENTRYPOINT ["python3"]
CMD ["web.py"]

# INSTRUCTIONS
# ============
# - Navigate to this directory
# - Build image with command `docker build -f newomf.dockerfile -t omfim .`
# - Run image in background with `docker run -d -p 5000:5000 --name omfcon omfim`
# - View at http://127.0.0.1:5000
# - Stop it with `docker stop omfcon` and remove it with `docker rm omfcon`.
# - Delete the images with `docker rmi omfim`
# 
# FEATURE IDEAS
# =============
# - Switch to install.py instead of manual apt commands
# - Python "build" script to create, start and exit the image
# - Modify Dockerfile to use a network drive containing the omf repo instead of doing a fresh git pull
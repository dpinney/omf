# A Dockerfile for running the Open Modeling Framework
# Tested on 2018-11-08 with Docker Version 18.06.1-ce-mac73 (26764)
FROM ubuntu:16.04
LABEL maintainer="<david.pinney@nreca.coop>"

# Install and setup OMF reqs
RUN apt-get -y update && apt-get install -y python sudo vim
RUN mkdir /home/omf
# TODO: just move install.py and run to setup environment then move the rest. Makes this more cacheable.
COPY install.py /home/omf/
COPY requirements.txt /home/omf/
COPY setup.py /home/omf/
COPY omf/scratch/GRIP/grip.py /home/omf/omf/
RUN cd /home/omf/; python install.py
# Put the rest of the source in there.
COPY omf /home/omf/omf

# Run the OMF
WORKDIR /home/omf/omf
ENTRYPOINT ["python"]
CMD ["-m", "grip"]
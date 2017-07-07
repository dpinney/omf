# A Dockerfile for running the Open Modeling Framework
FROM ubuntu:16.04
MAINTAINER <david.pinney@nreca.coop>

# Install and setup OMF reqs
RUN apt-get -y update && apt-get install -y python-pip git unixodbc-dev libfreetype6-dev pkg-config python-dev python-numpy alien python-pygraphviz python-pydot ffmpeg mdbtools python-cairocffi
RUN cd home; git clone https://github.com/dpinney/omf
RUN cd home/omf; python setup.py develop
# Make sure the docker instance listens externally:
RUN sed -i -e 's/host="127.0.0.1"/host="0.0.0.0"/g' /home/omf/omf/web.py

# Run the OMF
WORKDIR /home/omf/omf
ENTRYPOINT ["python"]
CMD ["web.py"]
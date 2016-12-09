# A Dockerfile for running the Open Modeling Framework
FROM ubuntu:16.04
MAINTAINER <mannanj90@gmail.com>

# Install and setup OMF reqs
RUN apt-get -y update && apt-get install -y python-pip git unixodbc-dev libfreetype6-dev pkg-config python-dev python-numpy alien python-pygraphviz python-pydot ffmpeg
RUN cd home; git clone https://github.com/dpinney/omf
RUN cd home/omf; python setup.py develop

# Run the OMF
WORKDIR /home/omf/omf
ENTRYPOINT ["python"]
CMD ["web.py"]
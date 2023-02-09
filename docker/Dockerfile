# Use an official Python runtime as a parent image
FROM continuumio/miniconda3

RUN apt-get --allow-releaseinfo-change update
RUN apt-get install -y build-essential 

RUN mkdir /tmp/cellmaps_utils
COPY ./ /tmp/cellmaps_utils/
RUN pip install /tmp/cellmaps_utils

RUN rm -rf /tmp/cellmaps_utils

ENTRYPOINT ["/opt/conda/bin/cellmaps_utilscmd.py"]

CMD ["--help"]

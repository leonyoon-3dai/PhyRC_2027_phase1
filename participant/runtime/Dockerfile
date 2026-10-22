FROM phyrc-2027:isaac-6.0.1
USER root
COPY requirements-additions.txt /opt/phyrc-pi05/requirements-additions.txt
RUN /isaac-sim/python.sh -m pip install --no-cache-dir --no-deps -r /opt/phyrc-pi05/requirements-additions.txt
COPY requirements-extra.txt /opt/phyrc-pi05/requirements-extra.txt
RUN /isaac-sim/python.sh -m pip install --no-cache-dir --no-deps -r /opt/phyrc-pi05/requirements-extra.txt
USER isaac-sim

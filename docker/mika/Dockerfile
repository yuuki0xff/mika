
FROM python:3.4.3

RUN pip3 install django==1.8.4 && \
	pip3 install --allow-all-external mysql-connector-python && \
	pip3 install SQLAlchemy==1.0.9 && \
	pip3 install uwsgi==2.0.11.2 && \
	rm -rf /tmp/pip_build_*

EXPOSE 3000

RUN useradd -u 1000 -s /bin/sh -m mika
ADD startup.sh /
CMD /bin/bash /startup.sh


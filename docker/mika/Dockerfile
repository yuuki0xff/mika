
FROM python:3.4.3

RUN pip3 install django && \
	pip3 install --allow-all-external mysql-connector-python && \
	pip3 install SQLAlchemy && \
	pip3 install uwsgi && \
	rm -rf /tmp/pip_build_*

EXPOSE 3000

ADD startup.sh /
CMD /bin/bash /startup.sh


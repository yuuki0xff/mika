
FROM python:3.4.3

RUN pip3 install django && \
	pip3 install --allow-all-external mysql-connector-python && \
	pip3 install SQLAlchemy && \
	pip3 install uwsgi && \
	rm -rf /tmp/pip_build_*

EXPOSE 3000


# FROM debian:wheezy

# RUN \
#     (echo wheezy main && \
#     echo wheezy-updates main && \
#     echo wheezy-proposed-updates main )| \
#         sed 's@^@deb http://hangup.dip.jp/cdn/debian @'>/etc/apt/sources.list && \
#     apt-get -y update && apt-get -y dist-upgrade && \
#     apt-get -y install python3-pip git

# FROM 77938750dea6
# RUN ln -s /usr/bin/pip-3.* /usr/local/bin/pip3
# RUN apt-get install curl
# RUN git clone --depth 1 https://github.com/yyuu/pyenv.git .pyenv && \
#     echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile && \
#     echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile && \
#     MAKEOPTS=-l6 pyenv install 3.4.3
#     echo 'export PATH="$PYENV_ROOT/versions/3.4.3/bin:$PATH"' >> ~/.profile && \

# RUN pip3 install django && \
#     pip3 install --allow-all-external mysql-connector-python && \
#     pip3 install SQLAlchemy && \
#     pip3 install uwsgi

ADD startup.sh /
CMD /bin/bash /startup.sh


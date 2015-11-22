#!/bin/bash
set -euv

REPOSITORY=${REPOSITORY:-https://github.com/yuuki0xff/mika}
export MIKA_DB_ADDR=${MYSQL_PORT_3306_TCP#tcp://}

#NGINX=${NGINX_PORT_80_TCP#tcp://}

#git clone $REPOSITORY /srv
cd /srv
#./manage.py syncdb

#mysql -uroot -proot <<EOS
#create database mika if not exists;
#EOS

exec uwsgi --ini ./core/uwsgi.ini


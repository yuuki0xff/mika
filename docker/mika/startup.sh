#!/bin/bash
set -euv
export MIKA_DB_ADDR=${MYSQL_PORT_3306_TCP#tcp://}

mkdir -pm 770 /run/mika
chown mika:mika /run/mika

su -mc '/srv/manage.py msgqueue_daemon' mika &
exec su -mc 'uwsgi --ini /srv/core/uwsgi.ini' mika


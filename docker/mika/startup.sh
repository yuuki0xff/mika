#!/bin/bash
set -euv

if ! [ ${MIKA_DB_ADDR:-} ]; then
	# set default value
	export MIKA_DB_ADDR=${MYSQL_PORT_3306_TCP#tcp://}
fi

useradd -u ${MIKA_UID} -s /bin/sh -m mika
mkdir -pm 770 /run/mika
chown mika:mika /run/mika

su -mc '/srv/manage.py msgqueue_daemon' mika &
su -mc 'uwsgi --ini /srv/core/uwsgi.ini' mika


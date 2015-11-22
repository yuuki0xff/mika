#!/bin/bash
set -euv
export MIKA_DB_ADDR=${MYSQL_PORT_3306_TCP#tcp://}

cd /srv
exec uwsgi --ini ./core/uwsgi.ini


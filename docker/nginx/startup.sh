#!/bin/sh
set -euv

file=/etc/nginx/conf.d/default.conf
cp ${file}.template ${file}

sed -i 's/${MIKA_ADDR}/'${MIKA_PORT_3000_TCP_ADDR}'/g' ${file}
sed -i 's/${MIKA_PORT}/'${MIKA_PORT_3000_TCP_PORT}'/g' ${file}
cat ${file}

exec nginx -g "daemon off;"


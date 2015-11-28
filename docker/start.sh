#!/bin/bash
set -euv
SELF=$(readlink -f $0)
ROOT_DIR=${SELF%/*/*}

DOCKER_MYSQL=mika/mysql:latest
DOCKER_NGINX=mika/nginx:latest
DOCKER_MIKA=mika/mika:latest

MYSQL_ROOT_PASSWORD=$(dd if=/dev/urandom|od -tx -w4 -An|head|tr -d ' \n')

MYSQL_CID=$(echo MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD} |
		docker run -dt \
		-v /var/lib/mysql \
		--env-file /dev/stdin \
		$DOCKER_MYSQL | cut -c1-12
)
sleep 10
docker exec -i $MYSQL_CID mysql -uroot -p$MYSQL_ROOT_PASSWORD <$ROOT_DIR/db.sql

MIKA_CID=$(echo MIKA_DB_AUTH=root:${MYSQL_ROOT_PASSWORD} |
	docker run -dt \
		-v $ROOT_DIR:/srv:ro \
		--link $MYSQL_CID:mysql \
		-e MIKA_DB_TYPE='mysql+mysqlconnector' \
		-e MIKA_DB_NAME=mika \
		--env-file /dev/stdin \
		$DOCKER_MIKA | cut -c1-12
)
NGINX_CID=$(docker run -dt \
	-v $ROOT_DIR:/srv:ro \
	--link $MIKA_CID:mika \
	-p 0.0.0.0:80:80 \
	$DOCKER_NGINX | cut -c1-12
)

echo MySQL Password: $MYSQL_ROOT_PASSWORD


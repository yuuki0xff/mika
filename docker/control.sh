#!/bin/bash
set -eu
SELF=$(readlink -f $0)
ROOT_DIR=${SELF%/*/*}
LOG_DIR=${ROOT_DIR}/log
mkdir -pm 700 $LOG_DIR

# Docker image names.
DOCKER_MYSQL=mika/mysql:latest
DOCKER_NGINX=mika/nginx:latest
DOCKER_MIKA=mika/mika:latest

# MySQL container settings.
USE_MYSQL_CONTAINER=1
MYSQL_ROOT_PASSWORD=root

# Mika container settings.
MIKA_DB_TYPE='mysql+pymysql'
MIKA_DB_AUTH=root:$MYSQL_ROOT_PASSWORD
# if not use MySQL container, you must set MIKA_DB_ADDR variable.
MIKA_DB_ADDR=                  # "<IP_ADDRESS>" or "<IP_ADDRESS>:<PORT>"
MIKA_DB_NAME=mika
MIKA_DB_OPT='charset=utf8mb4'  # parametor1=value1&parametor2=value2
# if not use Nginx container, you must set MIKA_HOST_PORT variable.
MIKA_HOST_PORT=                # "<PORT>" or "<IP_ADDRESS>:<PORT>"

# Nginx container settings.
USE_NGINX_CONTAINER=1
NGINX_HOST_PORT=0.0.0.0:80     # "<PORT>" or "<IP_ADDRESS>:<PORT>"

allContainer="mysql mika nginx"

LOG_BACKUP=1

INFO_DIR=/tmp/.mika-info-$UID
mkdir -pm 700 $INFO_DIR

getCID(){
	cat $INFO_DIR/$1
}

checkContainerStatus(){
	containerName=$1
	if [[ -f $INFO_DIR/$containerName ]]; then
		if [[ $(docker ps -q | grep "$(getCID "$containerName")") ]]; then
			return 0
		fi
	fi
	return 1
}

startContainer(){
	containerName=$1
	if checkContainerStatus $containerName; then
		killContainer $containerName
	fi
	case $containerName in
		mysql)
			(( $USE_MYSQL_CONTAINER )) || return
			echo MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD} |
				docker run -d \
					-v /var/lib/mysql \
					--env-file /dev/stdin \
					$DOCKER_MYSQL | cut -c1-12 >$INFO_DIR/$containerName
			sleep 10
			docker exec -i $(getCID mysql) mysql -uroot -p$MYSQL_ROOT_PASSWORD <$ROOT_DIR/db.sql
			;;
		mika)
			MIKA_ENV="
					MIKA_DB_TYPE=$MIKA_DB_TYPE
					MIKA_DB_AUTH=$MIKA_DB_AUTH
					MIKA_DB_ADDR=${MIKA_DB_ADDR:-}
					MIKA_DB_NAME=$MIKA_DB_NAME
					MIKA_DB_OPT=$MIKA_DB_OPT
					MIKA_UID=$UID"
			if [[ "${MIKA_HOST_PORT:-}" ]]; then
				MIKA_OPT="-p $MIKA_HOST_PORT:3000"
			fi
			echo "${MIKA_ENV}" |
				docker run -d \
					-v $ROOT_DIR:/srv:ro \
					-v $LOG_DIR:/srv/log \
					--link $(getCID mysql):mysql \
					--env-file /dev/stdin \
					${MIKA_OPT:-} \
					$DOCKER_MIKA | cut -c1-12 >$INFO_DIR/$containerName
			;;
		nginx)
			(( $USE_NGINX_CONTAINER )) || return
			docker run -d \
				-v $ROOT_DIR:/srv:ro \
				--link $(getCID mika):mika \
				-p $NGINX_HOST_PORT:80 \
				$DOCKER_NGINX | cut -c1-12 >$INFO_DIR/$containerName
			;;
	esac
}

killContainer(){
	containerName=$1
	if [[ -f $INFO_DIR/$containerName ]]; then
		docker kill $(cat $INFO_DIR/$containerName) || :
		rm -f $INFO_DIR/$containerName
	fi
}

attachContainer(){
	containerName=$1
	docker attach $(cat $INFO_DIR/$containerName)
}

execContainer(){
	containerName=$1
	shift
	docker exec -i $(cat $INFO_DIR/$containerName) "$@"
}



doAuto(){
	if ! checkContainerStatus mysql; then
		startContainer mysql
		startContainer mika
		startContainer nginx
	else
		startContainer mika
	fi
}

doAttach(){
	attachContainer "$@"
}

doStart(){
	target=${1:-all}
	shift
	case "$target" in
		all)
			for cn in $allContainer; do
				startContainer "$cn"
			done
			;;
		*)
			startContainer "$target"
			;;
	esac
}

doExec(){
	execContainer "$@"
}

doKill(){
	target=${1:-all}
	shift
	case "$target" in
		all)
			for cn in $allContainer; do
				killContainer "$cn"
			done
			;;
		*)
			killContainer "$target"
			;;
	esac
}

if (( $# )); then
	cmd=$1
	shift
	case "$cmd" in
		auto)
			if (( $LOG_BACKUP )) && [ "$(find $LOG_DIR/ -maxdepth 1 -name '*.log')" ]; then
				OLD_LOG_DIR=$LOG_DIR/$(date --rfc-3339=seconds |tr ' ' _)
				mkdir -p $OLD_LOG_DIR
				mv $LOG_DIR/*.log  $OLD_LOG_DIR
			fi
			doAuto
			;;
		attach)
			doAttach "$@"
			;;
		start)
			doStart "$@"
			;;
		exec)
			doExec "$@"
			;;
		kill)
			doKill "$@"
			;;
	esac
else
	(
	echo "Usage: $0 auto"
	echo "       $0 attach CONTAINER"
	echo "       $0 start [ all | CONTAINER ]"
	echo "       $0 exec CONTAINER CMD ARGS"
	echo "       $0 kill [ all | CONTAINER ]"
	) >&2
	exit 1
fi


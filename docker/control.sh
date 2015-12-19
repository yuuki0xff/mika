#!/bin/bash
set -eu
SELF=$(readlink -f $0)
ROOT_DIR=${SELF%/*/*}
LOG_DIR=${ROOT_DIR}/log
mkdir -pm 700 $LOG_DIR

DOCKER_MYSQL=mika/mysql:latest
DOCKER_NGINX=mika/nginx:latest
DOCKER_MIKA=mika/mika:latest

MYSQL_ROOT_PASSWORD=root #$(dd if=/dev/urandom|od -tx -w4 -An|head|tr -d ' \n')

allContainer="mysql mika nginx"

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
			echo MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD} |
				docker run -d \
					-v /var/lib/mysql \
					--env-file /dev/stdin \
					$DOCKER_MYSQL | cut -c1-12 >$INFO_DIR/$containerName
			sleep 10
			docker exec -i $(getCID mysql) mysql -uroot -p$MYSQL_ROOT_PASSWORD <$ROOT_DIR/db.sql
			;;
		mika)
			echo MIKA_DB_AUTH=root:${MYSQL_ROOT_PASSWORD} |
				docker run -d \
					-v $ROOT_DIR:/srv:ro \
					-v $LOG_DIR:/srv/log \
					--link $(getCID mysql):mysql \
					-e MIKA_DB_TYPE='mysql+mysqlconnector' \
					-e MIKA_DB_NAME=mika \
					-e MIKA_UID=$UID \
					--env-file /dev/stdin \
					$DOCKER_MIKA | cut -c1-12 >$INFO_DIR/$containerName
			;;
		nginx)
			docker run -d \
				-v $ROOT_DIR:/srv:ro \
				--link $(getCID mika):mika \
				-p 0.0.0.0:80:80 \
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


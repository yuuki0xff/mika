#!/bin/bash
set -euv
cd "${0%/*}"

REPOSITORY=mika
(cd mika;  docker build -t ${REPOSITORY}/mika: .)
(cd nginx; docker build -t ${REPOSITORY}/nginx: .)
(cd mysql; docker build -t ${REPOSITORY}/mysql: .)


#!/bin/bash
set -euv
cd "${0%/*}"
(cd mika; docker build -t mika/mika: .)
(cd nginx; docker build -t mika/nginx: .)
(cd mysql; docker build -t mika/mysql: .)


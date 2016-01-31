FROM mysql:5.5

RUN sed -ie 's/^bind-address\s*=\s.*$/bind-address = 0.0.0.0/' /etc/mysql/my.cnf && \
	( echo '[mysqld]'; \
	echo 'character-set-server = utf8mb4'; \
	echo '[mysql]'; \
	echo 'default-character-set = utf8mb4' )>/etc/mysql/conf.d/character_set.cnf

CMD ["mysqld"]


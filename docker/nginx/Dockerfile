
FROM nginx:1.9.7

EXPOSE 80 443

ADD default.conf.template /etc/nginx/conf.d/
ADD startup.sh /

CMD /startup.sh


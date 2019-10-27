#!/bin/bash -e

ALLOWED_HOSTS_SPACED=${ALLOWED_HOSTS/,/ }

sed -i -e "s/ALLOWED_HOSTS_SPACED/$ALLOWED_HOSTS_SPACED/" /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
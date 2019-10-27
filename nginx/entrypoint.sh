#!/bin/bash -e

# Prepare nginx config
ALLOWED_HOSTS_SPACED=${ALLOWED_HOSTS/,/ }
sed -i -e "s/ALLOWED_HOSTS_SPACED/$ALLOWED_HOSTS_SPACED/" /etc/nginx/conf.d/default.conf

# Install certificate
if [[ -d "/etc/letsencrypt/live/$ALLOWED_HOSTS" ]]; then
    echo "Install certificates"
    certbot install --nginx --cert-name "$ALLOWED_HOSTS" --redirect
    sleep 1
    nginx -s stop
    sleep 1
fi

exec nginx -g 'daemon off;'
FROM nginx:1.17

# Let's encrypt support
RUN apt-get update && apt-get install -y certbot python-certbot-nginx

COPY entrypoint.sh /app/
COPY default.conf /etc/nginx/conf.d/default.conf

ENTRYPOINT [ "/app/entrypoint.sh" ]
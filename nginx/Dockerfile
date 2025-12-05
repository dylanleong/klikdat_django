# Fetching the latest nginx image
#FROM nginx:1.23-alpine

FROM nginx

# Removing default nginx.conf
RUN rm /etc/nginx/conf.d/default.conf

# Copying our nginx.conf
COPY nginx.conf /etc/nginx/conf.d

# runs as nginx user
#RUN mkdir -p /etc/nginx/ssl/ && \
#    chown -R dylanleong:dylanleong /etc/nginx/ssl/ && \
#    chmod -R 755 /etc/nginx/ssl/
#USER dylanleong
#CMD ["nginx","-g","daemon off"]


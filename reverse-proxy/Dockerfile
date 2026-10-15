FROM nginx:latest

COPY nginx.conf /etc/nginx/nginx.conf
COPY proxy_params /etc/nginx/proxy_params
COPY proxy_params_websocket /etc/nginx/proxy_params_websocket

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]

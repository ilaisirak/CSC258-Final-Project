# service-gateway: edge API gateway / authorization layer.
#
# Pure nginx — no application code, no node build step. Terminates the
# public HTTP listener on :80, proxies API traffic to the backend
# services over mTLS, and reverse-proxies SPA traffic to
# service-frontend. The "service-frontend" container becomes
# cluster-internal only and serves static assets.
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

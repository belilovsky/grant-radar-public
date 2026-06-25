#!/usr/bin/env bash

set -euo pipefail

DOMAIN="${QAZ_FUND_DOMAIN:-qaz.fund}"
WWW_DOMAIN="${QAZ_FUND_WWW_DOMAIN:-www.qaz.fund}"
SERVER_IP="${QAZ_FUND_SERVER_IP:-}"
UPSTREAM="${QAZ_FUND_UPSTREAM:-http://127.0.0.1:8000}"
EMAIL="${QAZ_FUND_CERT_EMAIL:-}"
SITE_AVAILABLE="/etc/nginx/sites-available/${DOMAIN}.conf"
SITE_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}.conf"
CERT_PATH="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
PUBLIC_RESOLVERS=(
  "1.1.1.1"
  "8.8.8.8"
)

resolve_ipv4() {
  local host="$1"
  local resolver
  for resolver in "${PUBLIC_RESOLVERS[@]}"; do
    local answer
    answer="$(dig @"$resolver" +short A "$host" | tail -n 1)"
    if [[ -n "$answer" ]]; then
      echo "$answer"
      return 0
    fi
  done
  dig +short A "$host" | tail -n 1
}

ensure_http_site() {
  local tmp
  tmp="$(mktemp)"
  cat >"$tmp" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} ${WWW_DOMAIN};

    access_log /var/log/nginx/${DOMAIN}.access.log;
    error_log /var/log/nginx/${DOMAIN}.error.log;

    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

    client_max_body_size 16m;

    location / {
        proxy_pass ${UPSTREAM};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 120s;
    }
}
EOF
  install -m 644 "$tmp" "$SITE_AVAILABLE"
  rm -f "$tmp"
  ln -sfn "$SITE_AVAILABLE" "$SITE_ENABLED"
}

ensure_https_site() {
  local tmp
  tmp="$(mktemp)"
  cat >"$tmp" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} ${WWW_DOMAIN};

    access_log /var/log/nginx/${DOMAIN}.access.log;
    error_log /var/log/nginx/${DOMAIN}.error.log;

    location ^~ /.well-known/acme-challenge/ {
        root /var/www/certbot;
        allow all;
    }

    location / {
        return 301 https://${DOMAIN}\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${WWW_DOMAIN};

    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    return 301 https://${DOMAIN}\$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN};

    access_log /var/log/nginx/${DOMAIN}.access.log;
    error_log /var/log/nginx/${DOMAIN}.error.log;

    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    client_max_body_size 16m;

    location / {
        proxy_pass ${UPSTREAM};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 120s;
    }
}
EOF
  install -m 644 "$tmp" "$SITE_AVAILABLE"
  rm -f "$tmp"
  ln -sfn "$SITE_AVAILABLE" "$SITE_ENABLED"
}

main() {
  if [[ -z "$SERVER_IP" ]]; then
    echo "QAZ_FUND_SERVER_IP is not set." >&2
    exit 2
  fi

  if [[ -z "$EMAIL" ]]; then
    echo "QAZ_FUND_CERT_EMAIL is not set." >&2
    exit 2
  fi

  ensure_http_site
  nginx -t
  systemctl reload nginx

  local apex_ip
  apex_ip="$(resolve_ipv4 "$DOMAIN")"
  if [[ "$apex_ip" != "$SERVER_IP" ]]; then
    echo "${DOMAIN} is not pointed to ${SERVER_IP} yet; nginx HTTP site is ready."
    exit 0
  fi

  local www_ip=""
  www_ip="$(resolve_ipv4 "$WWW_DOMAIN")"

  if [[ ! -f "$CERT_PATH" ]]; then
    local domains=("-d" "$DOMAIN")
    if [[ "$www_ip" == "$SERVER_IP" ]]; then
      domains+=("-d" "$WWW_DOMAIN")
    fi

    certbot --nginx --non-interactive --agree-tos --redirect \
      --email "$EMAIL" "${domains[@]}"
  else
    echo "TLS certificate for ${DOMAIN} already exists."
  fi

  ensure_https_site

  nginx -t
  systemctl reload nginx
  echo "TLS is active for ${DOMAIN}."
}

main "$@"

#!/usr/bin/env bash
# One-time script to issue the first Let's Encrypt cert for tg.nexus-x.site.
# Run this ONCE on your VPS, from the project root, before bringing the full stack up with HTTPS.
#
#   chmod +x deploy/init-letsencrypt.sh
#   ./deploy/init-letsencrypt.sh
#
# Requirements:
#   - DNS A record for tg.nexus-x.site -> this server's public IP (already done)
#   - Ports 80 and 443 open on the VPS firewall / security group
#   - docker compose installed
set -euo pipefail

DOMAIN="tg.nexus-x.site"
EMAIL="${LETSENCRYPT_EMAIL:-admin@nexus-x.site}"   # override: LETSENCRYPT_EMAIL=you@you.com ./deploy/init-letsencrypt.sh
STAGING=0   # set to 1 to test against Let's Encrypt staging (avoids rate limits)

CERTBOT_DIR="./deploy/certbot"
CONF_DIR="$CERTBOT_DIR/conf"
WWW_DIR="$CERTBOT_DIR/www"
NGINX_CONF="./deploy/nginx/conf.d/tg.nexus-x.site.conf"
NGINX_CONF_BAK="${NGINX_CONF}.bak"

mkdir -p "$CONF_DIR" "$WWW_DIR"

echo "### Downloading recommended TLS params..."
if [ ! -e "$CONF_DIR/options-ssl-nginx.conf" ]; then
  curl -fsSL https://raw.githubusercontent.com/certbot/certbot/main/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$CONF_DIR/options-ssl-nginx.conf" || true
fi
if [ ! -e "$CONF_DIR/ssl-dhparams.pem" ]; then
  curl -fsSL https://raw.githubusercontent.com/certbot/certbot/main/certbot/certbot/ssl-dhparams.pem > "$CONF_DIR/ssl-dhparams.pem" || true
fi

echo "### Temporarily swapping nginx config to HTTP-only (so it can boot without certs)..."
cp "$NGINX_CONF" "$NGINX_CONF_BAK"
cat > "$NGINX_CONF" <<EOF
server {
  listen 80;
  server_name $DOMAIN;
  location /.well-known/acme-challenge/ { root /var/www/certbot; }
  location / { return 200 'bootstrap'; add_header Content-Type text/plain; }
}
EOF

echo "### Starting nginx (bootstrap mode)..."
docker compose up -d nginx
sleep 5

STAGING_FLAG=""
[ "$STAGING" -eq 1 ] && STAGING_FLAG="--staging"

echo "### Requesting Let's Encrypt certificate for $DOMAIN ..."
docker compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $STAGING_FLAG \
    --email $EMAIL \
    -d $DOMAIN \
    --rsa-key-size 4096 \
    --agree-tos \
    --no-eff-email \
    --non-interactive" certbot

echo "### Restoring real nginx config (HTTP + HTTPS)..."
mv "$NGINX_CONF_BAK" "$NGINX_CONF"

echo "### Reloading nginx..."
docker compose up -d --force-recreate nginx
docker compose up -d certbot

echo
echo "✅ Done. Test:  curl -I https://$DOMAIN"
echo "   If it works, bring everything up:  docker compose up -d --build"

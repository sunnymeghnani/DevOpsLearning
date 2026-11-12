#!/bin/bash
# t2: the system trust store trusts the internal CA, so curl verifies shop.example.com without -k.
fail() { echo "$1"; exit 1; }
R=(--resolve shop.example.com:443:127.0.0.1)
issuer=$(echo | openssl s_client -connect 127.0.0.1:443 -servername shop.example.com 2>/dev/null | openssl x509 -noout -issuer 2>/dev/null)
[[ "$issuer" == *"Example Internal CA"* ]] || fail "nginx no longer serves the certificate issued by Example Internal CA"
openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt /etc/nginx/ssl/shop.example.com.crt >/dev/null 2>&1 \
  || fail "the system CA bundle (/etc/ssl/certs/ca-certificates.crt) does not trust Example Internal CA"
out=$(env -i PATH=/usr/bin:/bin curl -q -sS "${R[@]}" --max-time 5 https://shop.example.com/health 2>&1)
[ "$out" = ok ] || fail "curl without -k: ${out:-no output}"
echo "curl verifies https://shop.example.com/health against the system trust store"

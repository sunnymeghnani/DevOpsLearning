#!/bin/bash
# t2: nginx serves the new certificate (reloaded), and a client that trusts that certificate verifies both names.
fail() { echo "$1"; exit 1; }
nginx -t -q 2>/dev/null || fail "nginx -t reports a configuration error"
systemctl is-active -q nginx || fail "nginx is not running"
systemctl is-enabled -q nginx || fail "nginx does not start at boot"
crt=$(nginx -T 2>/dev/null | sed -n 's/^[[:space:]]*ssl_certificate[[:space:]]\{1,\}\([^;]*\);.*/\1/p' | head -1)
[ -r "$crt" ] || fail "the configured certificate ${crt:-?} is missing"
served=$(echo | timeout 5 openssl s_client -connect 127.0.0.1:443 -servername shop.example.com 2>/dev/null | openssl x509 2>/dev/null)
[ -n "$served" ] || fail "nothing serves TLS on 127.0.0.1:443"
openssl x509 -noout -checkend 0 <<< "$served" >/dev/null 2>&1 || fail "nginx still serves the expired certificate: $(openssl x509 -noout -enddate <<< "$served")"
[ "$(openssl x509 -noout -fingerprint -sha256 <<< "$served")" = "$(openssl x509 -in "$crt" -noout -fingerprint -sha256)" ] \
  || fail "nginx serves a different certificate than $crt: reload nginx"
[ "$(openssl x509 -noout -subject -nameopt compat <<< "$served" | cut -d= -f2-)" = "$(openssl x509 -noout -issuer -nameopt compat <<< "$served" | cut -d= -f2-)" ] \
  || fail "the clients trust one self-signed certificate file; this one is signed by someone else"
for n in shop.example.com www.shop.example.com; do
  out=$(curl -q -sS --max-time 5 --cacert "$crt" --resolve "$n:443:127.0.0.1" -o /dev/null -w '%{http_code}' "https://$n/" 2>&1)
  [ "$out" = 200 ] || fail "a client that trusts $crt gets for https://$n/: $out"
done
echo "nginx serves the new certificate; https://shop.example.com/ and www verify"

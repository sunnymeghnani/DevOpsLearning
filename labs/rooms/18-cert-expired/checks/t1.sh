#!/bin/bash
# t1: the certificate file nginx is configured with is valid now (and for at least 30 days), names both hosts
# in its subjectAltName, and matches its private key.
fail() { echo "$1"; exit 1; }
crt=$(nginx -T 2>/dev/null | sed -n 's/^[[:space:]]*ssl_certificate[[:space:]]\{1,\}\([^;]*\);.*/\1/p' | head -1)
key=$(nginx -T 2>/dev/null | sed -n 's/^[[:space:]]*ssl_certificate_key[[:space:]]\{1,\}\([^;]*\);.*/\1/p' | head -1)
[ -n "$crt" ] && [ -n "$key" ] || fail "nginx has no ssl_certificate / ssl_certificate_key configured"
openssl x509 -in "$crt" -noout 2>/dev/null || fail "$crt is not a PEM certificate"
openssl x509 -in "$crt" -noout -checkend 0 >/dev/null 2>&1 || fail "$crt has expired ($(openssl x509 -in "$crt" -noout -enddate))"
nb=$(date -d "$(openssl x509 -in "$crt" -noout -startdate | cut -d= -f2)" +%s)
[ "$nb" -le "$(date +%s)" ] || fail "$crt is not valid yet (notBefore is in the future)"
openssl x509 -in "$crt" -noout -checkend 2592000 >/dev/null 2>&1 || fail "$crt expires within 30 days: issue it for longer"
san=$(openssl x509 -in "$crt" -noout -ext subjectAltName 2>/dev/null)
[ -n "$san" ] || fail "$crt has no subjectAltName: browsers ignore the CN, the names must be in the SAN"
for n in shop.example.com www.shop.example.com; do
  grep -q "DNS:$n\(,\|$\)" <<< "$san" || fail "the subjectAltName lacks DNS:$n"
done
[ -r "$key" ] || fail "$key is missing"
[ "$(openssl x509 -in "$crt" -noout -pubkey | sha256sum)" = "$(openssl pkey -in "$key" -pubout 2>/dev/null | sha256sum)" ] \
  || fail "$key does not belong to $crt"
[ $(( 0$(stat -c %a "$key") & 07 )) -eq 0 ] || fail "$key is readable by everyone: chmod 600"
echo "$crt is valid until $(openssl x509 -in "$crt" -noout -enddate | cut -d= -f2) for both names"

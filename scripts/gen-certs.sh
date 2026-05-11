#!/usr/bin/env bash
# Idempotently generates a self-signed dev CA and per-service certs
# under ./certs. See scripts/gen-certs.ps1 for the Windows version.
# These certs are FOR LOCAL DEVELOPMENT ONLY.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CERTS="$ROOT/certs"
mkdir -p "$CERTS"

FORCE="${1:-}"

SERVICES=(service-user service-auth service-class service-assignment service-grade-records service-submission service-enrollment service-bff service-file-storage service-gateway)

if [[ ! -f "$CERTS/ca.crt" || "$FORCE" == "--force" ]]; then
  echo "Generating dev CA..."
  openssl genrsa -out "$CERTS/ca.key" 4096 2>/dev/null
  openssl req -x509 -new -nodes -key "$CERTS/ca.key" -sha256 -days 3650 \
    -subj "/CN=csc258-dev-ca" -out "$CERTS/ca.crt"
else
  echo "CA already present (pass --force to regenerate)."
fi

for svc in "${SERVICES[@]}"; do
  if [[ -f "$CERTS/$svc.crt" && "$FORCE" != "--force" ]]; then
    echo "  $svc: existing cert kept"
    continue
  fi
  echo "  $svc: generating cert"
  cat > "$CERTS/$svc.ext" <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = $svc
DNS.2 = localhost
EOF
  openssl genrsa -out "$CERTS/$svc.key" 2048 2>/dev/null
  openssl req -new -key "$CERTS/$svc.key" -subj "/CN=$svc" -out "$CERTS/$svc.csr"
  openssl x509 -req -in "$CERTS/$svc.csr" -CA "$CERTS/ca.crt" -CAkey "$CERTS/ca.key" -CAcreateserial \
    -out "$CERTS/$svc.crt" -days 825 -sha256 -extfile "$CERTS/$svc.ext"
  rm -f "$CERTS/$svc.csr" "$CERTS/$svc.ext"
done

rm -f "$CERTS/ca.srl"
echo "Done. Certs in $CERTS"

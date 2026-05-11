# Idempotently generates a self-signed dev CA and per-service certs
# under ./certs. The CA is trusted by every container in compose; each
# service serves uvicorn TLS using its own cert and requires client
# certs signed by the same CA on inbound peer calls. The frontend
# (nginx gateway) acts as the TLS client to all backends.
#
# These certs are FOR LOCAL DEVELOPMENT ONLY. Do not deploy them.

param(
  [switch]$Force
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$certs = Join-Path $root "certs"
$conf  = Join-Path $certs "openssl.cnf"

New-Item -ItemType Directory -Force -Path $certs | Out-Null

if (-not (Get-Command openssl -ErrorAction SilentlyContinue)) {
  Write-Error "openssl not found on PATH. Install Git for Windows (which bundles openssl) or LibreSSL."
}

# Service list — each gets a server cert. service-gateway is included
# so the edge nginx can present a client cert when calling backends.
$services = @(
  "service-user",
  "service-auth",
  "service-class",
  "service-assignment",
  "service-grade-records",
  "service-submission",
  "service-enrollment",
  "service-bff",
  "service-file-storage",
  "service-gateway"
)

# 1. Root CA (skip if present unless -Force)
$caKey = Join-Path $certs "ca.key"
$caCrt = Join-Path $certs "ca.crt"
if ($Force -or -not (Test-Path $caCrt)) {
  Write-Host "Generating dev CA..."
  & openssl genrsa -out $caKey 4096 2>$null
  & openssl req -x509 -new -nodes -key $caKey -sha256 -days 3650 `
      -subj "/CN=csc258-dev-ca" -out $caCrt
} else {
  Write-Host "CA already present (use -Force to regenerate)."
}

# 2. Per-service certs
foreach ($svc in $services) {
  $key = Join-Path $certs "$svc.key"
  $csr = Join-Path $certs "$svc.csr"
  $crt = Join-Path $certs "$svc.crt"
  $ext = Join-Path $certs "$svc.ext"

  if ((-not $Force) -and (Test-Path $crt)) {
    Write-Host "  ${svc}: existing cert kept"
    continue
  }

  Write-Host "  ${svc}: generating cert"
  Set-Content -Path $ext -Encoding ascii -Value @"
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = $svc
DNS.2 = localhost
"@

  & openssl genrsa -out $key 2048 2>$null
  & openssl req -new -key $key -subj "/CN=$svc" -out $csr
  & openssl x509 -req -in $csr -CA $caCrt -CAkey $caKey -CAcreateserial `
      -out $crt -days 825 -sha256 -extfile $ext
  Remove-Item $csr, $ext -ErrorAction SilentlyContinue
}

Remove-Item (Join-Path $certs "ca.srl") -ErrorAction SilentlyContinue
Write-Host "Done. Certs in $certs"

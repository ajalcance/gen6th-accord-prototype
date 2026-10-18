# Owner applies to an application token; never a root/operator token.
# Existing derived key is created separately. No key creation rights.
path "transit/keys/accord-portraits" {
  capabilities = ["read"]
}
path "transit/encrypt/accord-portraits" {
  capabilities = ["update"]
}
path "transit/decrypt/accord-portraits" {
  capabilities = ["update"]
}

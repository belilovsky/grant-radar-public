# Vendored release dependencies

`qazstack-1.53.6-py3-none-any.whl` is the immutable wheel built from the
published QazStack release tag `v1.53.6` at commit
`553b78e54de11beefc2c4e01739bc28a2c0979a8`. It is intentionally checked in so
the QAZ.FUND production image can be rebuilt without a GitHub credential or a
runtime download from a private repository.

Its SHA-256 is recorded in `qazstack-1.53.6.sha256` using a path relative to
the repository root. Update both files only from a successful QazStack release
and cover the new contract with a QAZ.FUND integration test.

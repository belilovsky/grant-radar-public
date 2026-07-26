# Vendored release dependencies

`qazstack-1.41.2-py3-none-any.whl` is the immutable wheel built from the
published QazStack release tag `v1.41.2` at commit
`986cfca3779f74c0f734ed174e7a28c944fd30f7`. It is intentionally checked in so
the QAZ.FUND production image can be rebuilt without a GitHub credential or a
runtime download from a private repository.

Its SHA-256 is recorded in `qazstack-1.41.2.sha256` using a path relative to
the repository root. Update both files only from a successful QazStack release
and cover the new contract with a QAZ.FUND integration test.

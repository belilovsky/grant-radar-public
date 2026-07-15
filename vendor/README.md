# Vendored release dependencies

`qazstack-1.37.2-py3-none-any.whl` is the immutable wheel built from the
published QazStack release tag `v1.37.2`. It is intentionally checked in so
the QAZ.FUND production image can be rebuilt without a GitHub credential or a
runtime download from a private repository.

Its SHA-256 is recorded in `qazstack-1.37.2.sha256` using a path relative to
the repository root. Update both files only from a successful, tagged QazStack
release and cover the new contract with a QAZ.FUND integration test.

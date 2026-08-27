# QazLake opportunity consumer

The worker runs `scripts.sync_qazlake_opportunities.py`; it consumes only the
protected `qazlake.qazfund-opportunity-feed/v1` contract using
`QAZLAKE_QAZFUND_FEED_URL` and `QAZLAKE_PRODUCT_FEED_TOKEN`. The cursor is
private runtime state. The worker has no source adapter or external-fetch role.

Before enabling the consumer in production, replay the QazPipe feed, compare
stable source/external identities against the prior catalogue, then replace the
legacy scheduler with this worker. A feed/auth failure must leave the current
catalogue intact and fail the worker health check.

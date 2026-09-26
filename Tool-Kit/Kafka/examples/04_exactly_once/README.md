# 04: Exactly-Once Semantics (EOS) (Python)

## Concepts
- **Idempotent Producer**: Prevents duplicate messages on retries (`enable.idempotence=True`).
- **Transactions**: Atomic multi-partition writes (`transactional.id`).

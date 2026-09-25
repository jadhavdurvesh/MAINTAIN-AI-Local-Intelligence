# MAINTAIN AI Integration

Recommended production flow:

```text
MAINTAIN AI backend
        |
 authenticated local request
        v
Local Intelligence API
        |
 model inference
        v
structured evidence
        |
        v
MAINTAIN AI backend
        |
 Web / Desktop / Android / Gateway
```

The local node should not become the source of truth for organizations, users, machine assignments or work orders. Those remain in the main MAINTAIN AI platform.

## Example endpoint

`POST /api/inference/chronos2`

```json
{
  "machine_id": "MOTOR-001",
  "values": [1.0, 1.1, 1.0, 1.2],
  "horizon": 12
}
```

The initial local service is intentionally bound to `127.0.0.1`. For a gateway/industrial deployment, expose it only through a controlled private network path.

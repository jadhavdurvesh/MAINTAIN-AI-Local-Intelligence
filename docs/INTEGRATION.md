# MAINTAIN AI Integration

## 1. Integration principle

The local intelligence node should provide **evidence and forecasts**, not become a second system of record.

Recommended conceptual flow:

```text
Gateway / machine telemetry
          |
          v
Local Intelligence API
          |
      inference
          |
 structured evidence
          |
          v
Main MAINTAIN AI backend
          |
 +--------+---------+
 |        |         |
Web    Workforce   other clients
```

The exact transport between the main platform and this local node is not implemented in the current repository. The current local API is available through localhost for local callers.

## 2. Data contract

The core inference contract is:

```json
{
  "machine_id": "MOTOR-001",
  "values": [1.0, 1.1, 1.0, 1.2],
  "horizon": 12
}
```

The local service does not currently resolve `machine_id` against a central machine table. It treats the identifier as caller-provided context.

## 3. Result contract

Results can contain:

- model name;
- availability/readiness;
- statistical values;
- anomaly scores;
- forecast values;
- horizon/context information;
- reason text when a model is unavailable.

The analysis endpoint adds model collection, available-model list, anomaly index, and interpretation.

## 4. Business-system boundary

The local node should not own:

- organizations;
- users;
- technician accounts;
- machine assignments;
- work orders;
- maintenance schedules;
- enterprise notifications;
- enterprise audit records.

Those belong to the main MAINTAIN AI platform boundary.

## 5. Remote deployment

The current server binds to `127.0.0.1` intentionally. A future industrial/gateway deployment that requires remote calls should use a controlled private network path and an explicit authentication/authorization design.

Do not make the local API publicly reachable as a shortcut.

## 6. Recommended future integration envelope

A production integration should define:

```text
Caller identity
     |
request authorization
     |
asset identity
     |
time-series contract
     |
local inference
     |
result + model/version metadata
     |
platform ingestion
```

Model/version metadata is important so the main platform can distinguish results produced by different model revisions.

## 7. Failure behavior

Integration callers should treat a model `available=false` response as a model capability/readiness condition, not necessarily as a transport failure.

HTTP transport errors and model-runtime errors should remain distinguishable.

## 8. Current status

The repository implements the local side of the contract. It does not currently implement the authenticated remote connector described conceptually above.

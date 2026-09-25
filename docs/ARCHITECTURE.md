# MAINTAIN AI Local Intelligence — Architecture

## Position in the ecosystem

The local intelligence application is an edge/PC inference tier. It is not a replacement for the MAINTAIN AI hosted backend.

```text
Web / Desktop / Android / Gateway
              |
              v
       MAINTAIN AI backend
              |
     authenticated local API
              |
              v
   MAINTAIN AI Local Intelligence
       |        |        |
   TimeRadar Chronos-2  Timer
       |        |        |
       +---- baseline --+
              |
        local telemetry
```

## Runtime responsibilities

- Keep model execution close to the telemetry source when required.
- Avoid sending raw telemetry to a cloud inference service when local inference is preferred.
- Return structured evidence that the hosted application can combine with work-order, maintenance, fault and machine context.
- Keep authentication/authorization in the main MAINTAIN AI backend.

## Safety boundary

The local model service binds to `127.0.0.1` by default. Do not expose it directly to the public internet. LAN/industrial deployment should use an authenticated gateway and network controls.

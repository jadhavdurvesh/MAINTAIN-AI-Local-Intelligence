# Authentication, Authorization, and Security Boundary

## 1. Current implementation

This repository currently has **no user authentication system**.

There is no implementation here for:

- username/password login;
- Supabase Auth client/session handling;
- JWT validation;
- OAuth/OIDC;
- technician identity verification;
- roles or RBAC;
- machine-level permissions;
- API keys;
- signed requests;
- session cookies.

The wider ecosystem project map places identity and authorization in the main MAINTAIN AI backend / Supabase Auth. That is an external boundary from this repository.

## 2. What localhost provides

The FastAPI server defaults to:

```text
127.0.0.1:8000
```

This limits normal network reachability to the local machine. It does **not** authenticate the caller.

Think of the security layers as:

```text
Network boundary: localhost-only
        !=
Identity boundary: authentication
        !=
Authorization boundary: permissions
```

Only the first boundary exists in the current local engine by default.

## 3. Why this is acceptable for the current edge role

The engine is designed as a local inference runtime. Its primary expected callers are the desktop application and trusted local/edge processes.

Keeping identity out of the inference process also prevents the local engine from becoming a duplicate user-management system.

## 4. If remote access is introduced

A future integration that allows the main platform or another machine to call the local engine must explicitly define:

1. transport security;
2. caller authentication;
3. authorization scope;
4. replay protection where needed;
5. request validation;
6. rate limiting/resource limits;
7. audit logging;
8. secret/key storage;
9. failure behavior when the identity provider is unavailable.

Do not simply bind FastAPI to `0.0.0.0` and consider the service secure.

## 5. Relationship to technician authentication

Technician authentication belongs to the wider Workforce/main-platform identity flow. The local intelligence engine should receive only the identity/context it actually needs for a controlled operation, rather than implementing a second technician account database.

If a future requirement is to attribute an inference operation to a technician, the local API contract should carry a validated request context supplied by the trusted platform boundary, with explicit authorization rules. That is a future integration design, not current functionality.

## 6. Data and secrets

The current local engine stores telemetry/predictions in SQLite and model files on the local filesystem. It does not currently implement a secrets vault or user credential store.

Environment variables are used for configurable local paths/model IDs. They should not be treated as an authentication mechanism.

## 7. Security checklist for future expansion

Before exposing the service beyond localhost, implement and test:

- [ ] authenticated caller identity;
- [ ] authorization policy;
- [ ] TLS or a secure local/private transport;
- [ ] explicit allowed origins/hosts where relevant;
- [ ] request size and computational limits;
- [ ] audit events for privileged operations;
- [ ] safe model-download policy;
- [ ] filesystem permission review;
- [ ] model/checkpoint integrity verification;
- [ ] secure error responses that do not expose local paths/secrets.

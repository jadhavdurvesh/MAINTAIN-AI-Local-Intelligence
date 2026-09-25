# MAINTAIN AI Project Map

## Main platform

`Maintain.ai.3` is the primary MAINTAIN AI web/backend platform and system of record.

## Workforce client

The Android workforce application is the technician-facing mobile client for authentication, assigned machines, work orders and notifications.

## Local Intelligence

This repository is the PC/edge intelligence node. It runs selected models locally and provides inference results to the main platform through a controlled API.

## Gateway and firmware

The gateway/firmware layer connects industrial sensors and machines to the MAINTAIN AI ecosystem. It should feed telemetry into the platform/local intelligence layer rather than duplicating business logic.

## Design principle

Keep these responsibilities separate:

- identity and authorization: main MAINTAIN AI backend / Supabase Auth
- maintenance operations: main MAINTAIN AI backend
- local inference: this repository
- sensor acquisition: gateway/firmware
- technician interaction: Workforce Android app

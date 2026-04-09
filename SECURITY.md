# Security Policy

## Supported release posture

ME_CAM is intended to be deployed on user-controlled Raspberry Pi hardware or a user-controlled hosted dashboard. Public releases should include only production runtime code, documentation, and tests. Local lab artifacts, recovery scripts, bundled virtual environments, result dumps, and credentials are out of scope for public releases.

## Reporting a vulnerability

If you discover a security issue:

1. Do not publish exploit details or credentials.
2. Report the issue privately to the maintainer before public disclosure.
3. Include reproduction steps, affected files, impact, and any proposed fix.
4. Allow time for remediation before publishing details.

## Security controls implemented in V3

Application controls currently present in the codebase include:

- CSRF token generation and validation in `src/core/security.py` and `src/core/security_middleware.py`
- Request rate limiting for general traffic and login flows
- Security headers including CSP, referrer policy, frame protection, and permissions policy
- Password hashing through Werkzeug helpers
- Enrollment key creation, rotation, and constant-time verification in `src/core/user_auth.py`
- Input validation and sanitization helpers
- Release hygiene checks in `.github/workflows/release.yml`

## Security validation included in this repo

The test suite under `tests/test_security_layers.py` validates:

- CSRF generation and enforcement
- Rate limit behavior
- Security header application
- Password hashing and verification
- Enrollment key lifecycle behavior
- Input validation and sanitization behavior

These tests are designed to validate implemented controls. They are not a substitute for a full independent penetration test.

## Deployment guidance

For safer deployments:

- Use a fresh Raspberry Pi OS Lite image for Pi Zero 2W devices
- Rotate any credentials or enrollment keys before production use
- Avoid publishing example credentials or lab hostnames
- Keep the device behind HTTPS or a trusted reverse proxy when exposed remotely
- Remove local-only maintenance artifacts before creating a public release tag

## Non-goals

This repository does not claim parity with any commercial vendor by default. Security claims should be limited to controls that are implemented, tested, and documented in this codebase.

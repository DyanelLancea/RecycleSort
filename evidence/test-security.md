# Test 2: Security controls

- **Objective:** Verify authentication, input validation, brute-force protection, admin protection, network isolation and secret handling, each against a named threat from the CSA "Notorious Nine" (Lecture 5).
- **Setup:** `rs-alb`, `rs-app-asg` (2 x t3.medium), `rs-db` in private subnets with no public access. Firewall chain: `rs-alb-sg` (HTTP 80 from internet) → `rs-app-sg` (HTTP 80 from `rs-alb-sg` only) → `rs-db-sg` (PostgreSQL 5432 from `rs-app-sg` only). Repository commit `<paste latest commit hash>`.
- **Command/steps:** 7 checks run from AWS CloudShell, which is outside the VPC like a normal internet user. Full commands and output: `evidence/raw/test2-security-output.txt`.

| # | Check | Threat | Expected | Actual | Result |
| --- | --- | --- | --- | --- | --- |
| a | Upload with no login token | Insecure interfaces/APIs | 401 | 401 | PASS |
| b | Upload a text file named `.jpg` | Malicious upload | 400 | 400 "Corrupted or unreadable image" | PASS |
| c | 12 wrong passwords in a row | Account hijacking (brute force) | 401s, then 429 | 401 for tries 1–9, 429 from try 10 | PASS (see finding) |
| d | `GET /api/admin/logs` without `X-Admin-Key` | Insecure interfaces/APIs | 403 | 403 | PASS |
| e | TCP connect to the RDS endpoint on 5432 from outside the VPC | Data breach | Blocked | BLOCKED | PASS |
| f | `GET /health` on an app server's public IP, skipping the ALB | Bypassing the load balancer | Timeout | 000 (timeout) | PASS |
| g | `git grep` for access keys, private keys, lab passwords and RDS endpoints | Leaked secrets | No matches | No matches | PASS |

- **Expected result:** a) 401, b) 400, c) 401s followed by 429, d) 403, e) blocked, f) timeout, g) no matches.
- **Actual result:** All 7 checks matched the expected result. **Result: PASS.**
- **Date/time:** 2026-10-10 22:43 SGT (14:43 UTC)
- **Artefact path:** `evidence/raw/test2-security-output.txt`
- **Interpretation:** Every control blocked the threat it targets: only logged-in users can scan, invalid files are rejected, admin data needs the secret key from Parameter Store, the database cannot be reached from the internet, and app servers only accept traffic from the load balancer.
- **Finding and improvement (check c):** The login rate limiter stores attempt counts in each server's memory (limit 5 per server per minute). With 2 servers behind the ALB, requests were split between them and the correct login at the start also counted, so blocking started at attempt 10 instead of 6. In production, a shared counter (Amazon ElastiCache for Redis) or an AWS WAF rate-based rule would enforce one limit across all servers.

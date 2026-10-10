# Test 4: Scalability and resilience

- **Objective:** Show that the service (A) survives the loss of an app server and heals itself with no manual action, and (B) scales out under real load and scales back in when the load stops.
- **Setup:** `rs-alb` (internet-facing ALB, 2 public subnets in us-east-1a and us-east-1b) → target group `rs-app-tg` (health check `GET /health`, every 15 s, unhealthy after 2 failures) → Auto Scaling group `rs-app-asg` (min 2, desired 2, max 4, ELB health checks on, grace period 300 s, launch template `rs-app-lt` with AMI `rs-app-ami-v1`, t3.medium). Scaling policy `rs-cpu-60`: target tracking on average CPU utilisation, target 60%, instance warm-up 300 s. Database `rs-db` (RDS PostgreSQL, private subnets). Repository commit `<paste latest commit hash>`.
- **Expected result:** (A) Terminating one of the two servers causes at most a brief error window; the ASG launches a replacement automatically and the target group returns to 2 healthy targets. (B) Sustained load pushes average CPU above 60%, the target-tracking alarm fires, the ASG adds servers (up to 4), and after the load stops it removes them again, back to 2.

## Part A: Failure recovery (kill one server)

- **Steps:** From AWS CloudShell, `GET $ALB/health` was called once per second for 600 seconds. About 30 seconds in, app server `i-01bd33edfe4c2c525` (us-east-1b) was terminated manually in the EC2 console. Commands and output: `evidence/raw/test4a-health-loop.txt`, `evidence/raw/test4a-summary.txt`, `evidence/raw/test4a-asg-activity.txt`.

| Measure | Result |
| --- | --- |
| Health checks sent | 600 (1 per second for 10 minutes) |
| Successful (HTTP 200) | **593 (98.8%)** |
| Failed | 7: 3 x `502` and 4 x `000` (timeout), all between 15:06:54 and 15:07:17 UTC (about 23 seconds) |
| Replacement launched | 15:07:43 UTC, `i-0335335aac3150e54` (us-east-1a), cause "an unhealthy instance needing to be replaced" |
| Back to 2 healthy targets | Yes, within about 5 minutes |
| Manual action needed | None |
| SNS alert | Email "Auto Scaling: launch for group rs-app-asg" received at 15:07:48 UTC |

- **Interpretation:** The load balancer kept the service available on the remaining server, and the Auto Scaling group replaced the lost one automatically (Lecture 3, failure recovery). The short error window exists because the ALB only marks a target unhealthy after 2 failed checks 15 seconds apart, so for up to about 30 seconds some requests still went to the dead server. **Improvement:** a 5-second health-check interval would cut this window to about 10 seconds.

## Part B: Scale out and scale in under real load

- **Steps:** From AWS CloudShell, `tests/load_test.py` registered a synthetic user (`load-...@example.com`) and sent image uploads (`tests/samples/can.jpg`) from 20 concurrent workers, non-stop, for 900 seconds (15:27:20 to 15:42:22 UTC). Each upload runs a full ResNet50 inference, so the load is real CPU work rather than an artificial threshold change. Commands and output: `evidence/raw/test4b-load-output.txt`, `evidence/raw/test4b-peak-4-servers.txt`, `evidence/raw/test4b-asg-activity.txt`.

| Measure | Result |
| --- | --- |
| Requests | **9,674** in 15 minutes (about 10.7 per second) |
| Successful (HTTP 200) | **9,654 (99.79%)** |
| Failed | 20 (0.21%): 11 x `504` gateway timeout, 9 connection errors |
| Response time p50 / p95 | **0.84 s / 3.92 s** |
| Average CPU | About 0.5% before the test, about 70% during it |

| Time (UTC) | Scaling event (from the ASG activity history) |
| --- | --- |
| 15:32:36 | `AlarmHigh` in ALARM, policy `rs-cpu-60` sets desired capacity 2 → 3 |
| 15:39:36 | `AlarmHigh` in ALARM again, desired capacity 3 → 4 |
| about 15:48 | 4 targets healthy, 2 in us-east-1a and 2 in us-east-1b |
| 15:57:50 | `AlarmLow` in ALARM, desired capacity 4 → 3 |
| 15:59:10 | `AlarmLow` in ALARM, desired capacity 3 → 2 ("At desired capacity") |

- **Interpretation:** The target-tracking policy reacted to real demand without any manual change: it doubled capacity from 2 to 4 servers across both Availability Zones while 99.8% of requests succeeded, then returned to 2 servers about 16 minutes after the load ended, which keeps cost down when demand is low (Lecture 3, elasticity). Average CPU stayed around 70% after scale-out because the test is closed-loop: each worker sends its next request as soon as the previous one returns, so extra servers increased throughput rather than lowering CPU. With real users who pause between scans, extra servers would lower CPU instead.
- **Findings and improvements:**
  - The 20 failed requests and the 3.9 s p95 happened mostly while only 2 servers were handling the load, before the new servers finished their 300 s warm-up. A lower CPU target (e.g. 50%) or a step-scaling policy would add capacity sooner.
  - New servers load the 225 MB model on their first request (about 10 s). Loading it at service start-up would let a new server serve traffic faster.
  - Scale-in took about 16 minutes, because target tracking waits for 15 consecutive low datapoints before removing capacity. This is deliberately cautious, to avoid flapping.

- **Date/time:** 2026-10-10 23:06–00:00 SGT (15:06–16:00 UTC)
- **Artefact path:** `evidence/raw/test4a-health-loop.txt`, `evidence/raw/test4a-summary.txt`, `evidence/raw/test4a-asg-activity.txt`, `evidence/raw/test4b-load-output.txt`, `evidence/raw/test4b-peak-4-servers.txt`, `evidence/raw/test4b-asg-activity.txt`; screenshots in `evidence/screenshots/2026-10-10-test4*.png`
- **Result: PASS** (both parts).

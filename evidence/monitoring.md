# Monitoring and operations

**Summary:** RecycleSort is monitored with Amazon CloudWatch (metrics, dashboard, alarms, logs) and Amazon SNS (email alerts). During testing on 10 Oct 2026, the monitoring detected a server failure (Test 4A) and a CPU overload (Test 4B), and the alarms drove automatic recovery and scaling with no manual action.

## 1. Dashboard `rs-dashboard`

| Widget | Metrics (namespace) | Statistic, period | Why it matters |
| --- | --- | --- | --- |
| Traffic and errors | RequestCount, HTTPCode_Target_2XX_Count, HTTPCode_ELB_5XX_Count, HTTPCode_Target_5XX_Count (AWS/ApplicationELB, `rs-alb`) | Sum, 1 min | Demand and error rate seen by users |
| Response time | TargetResponseTime (AWS/ApplicationELB) | Average and p95, 1 min | User experience; p95 used in Test 4B |
| Healthy servers | HealthyHostCount, UnHealthyHostCount (AWS/ApplicationELB, `rs-app-tg`) | Maximum, 1 min | Shows failure and recovery (Test 4A) |
| Number of servers | GroupInServiceInstances, GroupDesiredCapacity (AWS/AutoScaling, `rs-app-asg`) | Maximum, 1 min | Shows scale-out 2 → 4 and scale-in 4 → 2 (Test 4B) |
| App server CPU | CPUUtilization (AWS/EC2, by Auto Scaling group `rs-app-asg`) | Average, 1 min | The metric the scaling policy tracks (target 60%) |
| Database | CPUUtilization, DatabaseConnections (AWS/RDS, `rs-db`) | Average, 1 min | Database load and connection use |

Screenshots: `evidence/screenshots/2026-10-10-test4b-dashboard-cpu-high.jpg`, `evidence/screenshots/2026-10-10-test4b-dashboard-after.jpg` 

## 2. Alarms

| Alarm | Metric and condition | Action | Observed on 10 Oct 2026 |
| --- | --- | --- | --- |
| `rs-unhealthy-hosts` | UnHealthyHostCount (`rs-app-tg`), Maximum >= 1 for 1 x 1 min, missing data = not breaching | SNS `rs-alerts` | Stayed OK: the ALB removed the terminated instance before it counted as unhealthy |
| `rs-target-5xx` | HTTPCode_Target_5XX_Count (`rs-alb`), Sum > 5 in 5 min, missing data = not breaching. Created with the AWS CLI (`src/infra/create-alarms.sh`) because the metric only exists after the first 5xx | SNS `rs-alerts` | Stayed OK: no 5xx from the app during the tests (the 11 x 504 in Test 4B were returned by the load balancer, not the app) |
| `rs-db-cpu-high` | CPUUtilization (`rs-db`), Average > 80% for 1 x 5 min | SNS `rs-alerts` | Stayed OK: database CPU stayed low even at 9,674 requests in 15 min |
| `TargetTracking-rs-app-asg-AlarmHigh-…` | Created by policy `rs-cpu-60`: CPUUtilization > 60 for 3 datapoints within 3 min | Scale out | ALARM at 15:32:36 and 15:39:36 UTC → capacity 2 → 3 → 4 |
| `TargetTracking-rs-app-asg-AlarmLow-…` | Created by policy `rs-cpu-60`: CPU well below target for 15 datapoints | Scale in | ALARM at 15:57:50 and 15:59:10 UTC → capacity 4 → 3 → 2 |

Screenshot: `evidence/screenshots/2026-10-10-test4b-alarmhigh-graph.jpg` (CPU line above the 60% threshold, two ALARM periods, back to OK).

## 3. Notifications (Amazon SNS `rs-alerts`)

- Email subscription confirmed; delivery verified with a test message.
- Auto Scaling activity notifications (launch/terminate) are sent to the same topic.
- Example received during Test 4A: "Auto Scaling: launch for group rs-app-asg", 15:07:48 UTC, cause "an unhealthy instance needing to be replaced". Screenshot (account ID removed): `evidence/screenshots/2026-10-10-test4a-sns-launch-email.jpg`.

## 4. Logs (CloudWatch Logs)

The CloudWatch agent (`src/infra/cloudwatch-agent-config.json`) on every app server ships two log files, retention 7 days, one stream per instance:

| Log group | Source | Contents |
| --- | --- | --- |
| `/recyclesort/app` | `/var/log/recyclesort/app.log` | FastAPI/uvicorn output and errors |
| `/recyclesort/nginx-access` | `/var/log/nginx/access.log` | Every HTTP request: time, method, path, status |

**Operational query (Logs Insights, log group `/recyclesort/nginx-access` only):**

```text
fields @timestamp, @message
| filter @message like /POST \/api\/upload/
| stats count() as uploads by bin(5m)
```

**Result (log group `/recyclesort/nginx-access`, 10 Oct 2026 14:00–16:30 UTC, exported from Logs Insights):**

| 5-minute window (UTC) | SGT | Uploads (`POST /api/upload`) | What was happening |
| --- | --- | --- | --- |
| 14:20 | 22:20 | 1 | Warm-up scan after resuming the lab |
| 14:30 | 22:30 | 1 | Test 1: functional workflow |
| 14:40 | 22:40 | 2 | Test 2: upload without login (401) and fake image (400) |
| 14:55 | 22:55 | 10 | Test 3: live AI validation, one image per class |
| 15:25 | 23:25 | 1,430 | Test 4B: load test starts (15:27:20) |
| 15:30 | 23:30 | 2,739 | Test 4B: 2 → 3 servers at 15:32 |
| 15:35 | 23:35 | 4,273 | Test 4B: peak, 3 → 4 servers at 15:39 |
| 15:40 | 23:40 | 1,232 | Test 4B: load test ends (15:42:22) |
| **Total during load test** | | **9,674** | Matches `evidence/raw/test4b-load-output.txt` exactly |

Windows with no uploads are not shown.

**Interpretation:** The query counts every scan request per 5-minute window from the web server's own access logs. It independently confirms each test: the 9,674 uploads logged during Test 4B match the load-test script's count exactly, and the busiest window (4,273 uploads in 15:35–15:40) is when the service had scaled out to 3–4 servers. The same query could support an operational decision, such as which times of day need more capacity.

Note: the client IP addresses in the nginx log are personal data under the PDPA, so access to the log group is restricted to the AWS account and logs are kept for only 7 days.

## 5. Interpretation

- **Detection:** CPU, healthy-host and error metrics showed both incidents within 1 minute.
- **Automatic response:** health checks replaced the failed server (Test 4A), and the target-tracking alarms added and then removed capacity (Test 4B). No human action was needed.
- **Limitation:** alerts go to email only, and there is no alarm on response time. Improvement: add an alarm on TargetResponseTime p95 > 2 s, and route alerts to a chat channel.

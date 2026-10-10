# Cost log

Account: AWS Academy Learner Lab (credit-based). Region: us-east-1.

## Learner Lab budget readings

Readings are copied from the budget figure on the AWS Academy Learner Lab page. The Learner Lab does not update this figure in real time; spend usually appears several hours later.

| Date/time (SGT) | Budget figure shown (USD) | Note |
| --- | --- | --- |
| 10 Oct ~12:40 | 10.80 | Before building anything |
| 10 Oct ~15:35 | Not recorded | After build; paused (ASG to 0, database stopped) |
| 11 Oct 01:25 | 10.80 | After all 4 tests. Unchanged: the Learner Lab had not yet reported the day's spend |
| 11 Oct <!-- time --> | <!-- fill in --> | Final reading, before teardown |

**Measured spend:** <!-- difference between the first and final reading, once the panel updates. If it never changes, replace this line with: "The Learner Lab budget figure did not update within the project window, so actual spend could not be measured; see the estimate below." -->

## Estimated spend

| Item | Approx. USD per hour (us-east-1 on-demand) |
| --- | --- |
| 2 x EC2 t3.medium (up to 4 during the load test) | 0.08 (up to 0.17) |
| Application Load Balancer | 0.03 |
| RDS PostgreSQL db.t4g.micro | 0.02 |
| Public IPv4 addresses, EBS, S3, CloudWatch, SSM | about 0.03 |
| **Total while running** | **about 0.15–0.25** |

| Period (SGT) | State | Approx. hours | Approx. cost (USD) |
| --- | --- | --- | --- |
| 10 Oct 12:40–15:35 | Building (build server, then ALB + 2 servers + database) | 3 | 0.45–0.75 |
| 10 Oct 15:35–22:10 | Paused: no app servers, database stopped; only the ALB, storage and public IPs still billed | 6.5 | about 0.30 |
| 10 Oct 22:10–11 Oct 01:30 | Testing (2 servers, up to 4 during the 15-minute load test) | 3.3 | 0.50–0.80 |
| **Total** | | | **roughly USD 1.25–1.85** |

These are rough estimates from approximate on-demand prices, not measured values.

## Cost controls used

- **No NAT gateway** (saves about USD 1 per day per gateway); only the database is in private subnets, and it needs no internet access.
- **S3 gateway endpoint** (free) instead of paid interface endpoints.
- **Right-sized instances:** t3.medium app servers (the smallest size that fits TensorFlow and ResNet50 in memory) and a db.t4g.micro database.
- **Auto Scaling minimum of 2** and automatic scale-in after load (4 → 2 within about 16 minutes in Test 4B).
- **Build server terminated** after the AMI was created.
- **Paused between sessions:** ASG set to 0 and the database stopped (10 Oct 15:35–22:10, and after testing).
- **Log retention 7 days** on both log groups.
- **Full teardown after submission** (checklist in the plan, Section 6).

## Sustainability notes

- Servers are only added when CPU demand requires it, and removed when it drops.
- The database runs on AWS Graviton (db.t4g.micro), which AWS describes as more energy-efficient than comparable x86 instances.
- The app servers could also move to Graviton (t4g); this would need ARM builds of TensorFlow and a rebuilt AMI.
# Data dictionary

Synthetic fields used by RecycleSort. No live student or production waste images are stored in this repository.

## `users`

| Field | Type | Description |
| --- | --- | --- |
| id | integer, PK | Internal user identifier |
| email | string, unique | Login identity |
| password_hash | string | bcrypt hash; never store plaintext |
| points | integer | Cumulative gamification score |
| created_at | timestamp | Account creation time (UTC) |

## `scan_logs`

| Field | Type | Description |
| --- | --- | --- |
| id | integer, PK | Scan identifier |
| user_id | integer, FK → users.id | Who submitted the image |
| predicted_class | string | One of `battery`, `biological`, `cardboard`, `clothes`, `glass`, `metal`, `paper`, `plastic`, `shoes`, or `trash` |
| confidence | float | Model confidence in `[0, 1]` |
| is_recyclable | boolean | Recyclable decision after class rules |
| points_awarded | integer | Points granted for this scan |
| created_at | timestamp | Scan time (UTC) |
| image_filename | string, nullable | Original uploaded image filename; image bytes are not stored |

## `data/sample_scans.csv`

| Field | Type | Description |
| --- | --- | --- |
| image_id | string | Synthetic filename stem |
| material | string | Ground-truth class; one of the 10 classes listed for `scan_logs.predicted_class` |
| contaminated | boolean | If true, item should not be treated as recyclable |
| split | string | `train` or `test` |

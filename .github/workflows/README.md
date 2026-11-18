# Scheduled jobs

| Workflow | Schedule | What it does |
| --- | --- | --- |
| `ingest-readings.yml` | hourly at :10 | Downloads `s3://$AWS_S3_BUCKET/gym_crowd.csv` and upserts new rows into `crowd_readings` |
| `daily-forecast.yml` | 05:00 SGT (21:00 UTC) | Downloads `models/gym_crowd_model_$MODEL_VERSION.joblib`, fetches the Open-Meteo forecast once, writes 30-min `daily_batch` predictions for today's opening hours |

Both can also be started by hand from the Actions tab (`workflow_dispatch`); the forecast takes an optional `date`.

## Repository settings → Secrets and variables → Actions

**Secrets**

| Name | Value |
| --- | --- |
| `AWS_ACCESS_KEY_ID` | Same IAM user key the Render build uses |
| `AWS_SECRET_ACCESS_KEY` | 〃 |
| `AWS_ROLE_ARN` | Role the key assumes (same as Render) |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Project Settings → API → `service_role` |

**Variables**

| Name | Example |
| --- | --- |
| `AWS_REGION` | `ap-southeast-1` |
| `AWS_S3_BUCKET` | your bucket name |
| `SUPABASE_URL` | `https://<project-ref>.supabase.co` |
| `MODEL_VERSION` | `v1` — keep in sync with Render's `MODEL_VERSION` |

## IAM

The role needs read access to both objects:

```json
{
  "Effect": "Allow",
  "Action": "s3:GetObject",
  "Resource": [
    "arn:aws:s3:::<bucket>/gym_crowd.csv",
    "arn:aws:s3:::<bucket>/models/*"
  ]
}
```

## Running locally (from `backend/`)

```bash
python -m app.jobs ingest --csv ../path/to/gym_crowd.csv
MODEL_VERSION=v1 python -m app.jobs forecast --date 2026-11-18
```

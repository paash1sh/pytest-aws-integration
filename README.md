# pytest-aws-integration

End-to-end integration test suite validating the full cloud deployment stack for a banking application. Tests cover the API → Lambda → S3 → RDS flow, response time SLAs, concurrent request handling, and cloud infrastructure health checks.

## Tech Stack

- Python 3.11
- pytest 7.4.0
- boto3 1.26.x
- requests 2.31.0
- GitHub Actions (scheduled + push triggers)
- AWS (Lambda, S3, RDS PostgreSQL)

## Test Coverage

| Area | Tests |
|------|-------|
| API → Lambda flow | Transaction triggers Lambda processing |
| S3 storage | Receipt stored after transaction |
| Response SLA | API responds within 1.5s |
| Concurrency | 5 concurrent requests handled correctly |
| Lambda cold start | Cold start under 5s |
| S3 health | Bucket accessible |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# add AWS credentials and resource names
```

## Running Tests

```bash
pytest tests/ -v
pytest tests/ -v --html=reports/report.html
```

## CI/CD

GitHub Actions runs on every push to `main` and on a scheduled cron (`Mon–Fri 6am UTC`) to catch environment drift overnight.

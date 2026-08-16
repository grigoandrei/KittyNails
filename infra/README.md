# KittyNails — AWS Infrastructure (CDK)

CDK stack that deploys the KittyNails booking app to AWS.

## Architecture

```
React (S3 + CloudFront) ──▶ CloudFront /api/* ──▶ API Gateway ──▶ Backend Lambda ──▶ RDS PostgreSQL
                                                                        │              (private subnet)
                                                                        ├──▶ Bedrock (AI)
                                                                        ├──▶ SES (email)
                                                                        └──▶ Stripe (via NAT instance)

EventBridge (hourly) ──▶ Reminder Lambda ──▶ RDS + SES
```

- **VPC** — 2 AZs, public + private subnets. Egress via a **NAT instance** (`t4g.nano`, ~$3–4/mo) instead of a managed NAT Gateway (~$32/mo).
- **RDS PostgreSQL** — `t4g.micro`, private subnet, **no public access**. Credentials auto-generated into Secrets Manager (`kittynails/db`).
- **Secrets Manager** — `kittynails/db` (DB creds) + `kittynails/app` (JWT, admin, Stripe keys).
- **Lambdas** — backend (FastAPI/Mangum) + reminder, both container images in the VPC.
- **API Gateway** — REST API proxy to the backend Lambda.
- **CloudFront + S3** — serves the React build; `/api/*` routes to API Gateway (so the frontend uses relative paths, no CORS).

Estimated cost: **~$20–25/mo** (mostly the NAT instance EC2; RDS `t4g.micro` is free-tier eligible for the first 12 months).

## Prerequisites

- AWS CLI configured with credentials for the target account
- Docker running (CDK builds the Lambda container image locally)
- Node.js (for the `cdk` CLI) and Python 3.12
- `npx aws-cdk` or a globally installed `cdk`

## Setup

```bash
cd infra
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# One-time per account/region
npx cdk bootstrap
```

## Deploy

```bash
# From infra/, with the venv active
npx cdk synth      # verify the stack compiles
npx cdk deploy     # deploy (builds the Lambda image, provisions everything)
```

Outputs printed on success:
- `ApiUrl` — the raw API Gateway URL
- `CloudFrontUrl` — the public site URL
- `FrontendBucketName` — S3 bucket for the frontend build

## Post-deploy steps (required)

### 1. Populate the app secret
The `kittynails/app` secret is created with an auto-generated `JWT_SECRET` and empty placeholders. Fill in the real values:

```bash
aws secretsmanager put-secret-value --secret-id kittynails/app --secret-string '{
  "ADMIN_USERNAME": "cata",
  "ADMIN_PASSWORD_HASH": "<bcrypt hash>",
  "JWT_SECRET": "<keep the generated one or set your own>",
  "STRIPE_SECRET_KEY": "sk_live_...",
  "STRIPE_PUBLISHABLE_KEY": "pk_live_...",
  "STRIPE_WEBHOOK_SECRET": "whsec_..."
}'
```

Also set `FRONTEND_URL` and `SES_SENDER_EMAIL` — either add them to the app secret and extend `_load_aws_secrets()`, or set them as Lambda environment variables in the stack. `FRONTEND_URL` **must** be your CloudFront/custom domain so Stripe redirects work.

### 2. Run database migrations
The DB is private, so run Alembic from within the VPC. Options:
- **Bastion / SSM session** into a host in the VPC, then `alembic upgrade head` with `DATABASE_URL` built from the `kittynails/db` secret.
- **One-off ECS task** or a temporary migration Lambda.

> ⚠️ Migration `d4e5f6a7b8c9` uses `ALTER TYPE ... ADD VALUE`, which cannot run inside a transaction on some PostgreSQL setups. If Alembic wraps migrations in a transaction, run this one with `op.execute` outside the transaction or apply it manually. Test against RDS before go-live.

### 3. Build & upload the frontend
```bash
cd ../frontend
npm run build
aws s3 sync dist/ s3://<FrontendBucketName>/ --delete
# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id <DIST_ID> --paths "/*"
```

The frontend uses relative `/api` paths, which CloudFront routes to API Gateway — no extra config needed.

### 4. SES production access
- Verify the sender domain/email (`noreply@kittynails.de`) in SES
- Request **production access** (out of sandbox) so you can email real clients
- Until then, `SES_ENABLED=true` will only deliver to verified addresses

### 5. Stripe production webhook
- In the Stripe dashboard, add a webhook endpoint: `https://<your-domain>/api/webhooks/stripe`
- Subscribe to `checkout.session.completed` and `checkout.session.expired`
- Copy the live signing secret into the `kittynails/app` secret (`STRIPE_WEBHOOK_SECRET`)

### 6. Custom domain (optional)
- Request an ACM certificate for `kittynails.de` (**us-east-1** for CloudFront)
- Add the domain + cert to the CloudFront distribution
- Point DNS (Route 53 or your registrar) at the CloudFront distribution

## Tearing down

```bash
npx cdk destroy
```

Note: RDS has `deletion_protection=True` and a `SNAPSHOT` removal policy — you'll need to disable protection / handle the final snapshot manually. The frontend S3 bucket auto-deletes its objects.

## Notes / gotchas

- **`AWS_REGION` is reserved in Lambda** — the stack injects `AWS_REGION_NAME` instead; `config.py` reads either.
- **Secrets are loaded at cold start** via `_load_aws_secrets()` in `config.py`. Local dev (no `DB_SECRET_ARN`) falls back to `.env`.
- **NAT instance** is a single point of failure (one AZ). Fine for this scale; for HA you'd run one per AZ (more cost).
- **Cold starts** — container-image Lambdas in a VPC have ~1–3s cold starts. Acceptable for this traffic; add provisioned concurrency if needed.

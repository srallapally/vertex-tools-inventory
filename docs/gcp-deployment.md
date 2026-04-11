# GCP Deployment Guide for Vertex Tools Inventory

This document describes how to deploy the offline inventory job to GCP so it runs on a schedule, writes inventory artifacts to Google Cloud Storage, and can later be read by the connector.

## Target architecture

Use this execution flow:

`Cloud Scheduler -> Cloud Run Job -> GCS bucket -> connector reads artifacts from GCS`

This keeps IAM/resource discovery out of the connector reconciliation path and moves collection into a scheduled batch job.

## Produced artifacts

Each job run should write these files:

- `agents.json`
- `identity-bindings.json`
- `service-accounts.json`
- `manifest.json`

## Recommended artifact layout

Store artifacts in both an immutable run-specific prefix and an optional stable `latest` prefix.

```text
gs://<BUCKET>/<PREFIX>/runs/<TIMESTAMP>/
  agents.json
  identity-bindings.json
  service-accounts.json
  manifest.json

gs://<BUCKET>/<PREFIX>/latest/
  agents.json
  identity-bindings.json
  service-accounts.json
  manifest.json
```

Example:

```text
gs://my-inventory-bucket/vertex-inventory/runs/2026-04-11T08-31-46Z/
  agents.json
  identity-bindings.json
  service-accounts.json
  manifest.json

gs://my-inventory-bucket/vertex-inventory/latest/
  agents.json
  identity-bindings.json
  service-accounts.json
  manifest.json
```

## Why this layout

The run-specific prefix gives you:

- immutable snapshots
- easier troubleshooting
- auditability
- rollback if the latest run is bad

The `latest` prefix gives the connector a stable read location.

## Runtime model

The job should:

1. collect inventory into local files under `/tmp/out`
2. validate or complete the local artifact set
3. upload the files to the run-specific GCS prefix
4. optionally copy/promote the same files to the `latest` prefix

Do not write partial artifacts directly into `latest/`.

## GCP services used

- **Cloud Run Jobs**: batch execution of the inventory job
- **Cloud Scheduler**: scheduled triggering of the job
- **Cloud Storage**: durable artifact storage
- **Artifact Registry** or **Container Registry**: container image storage
- **Cloud Build**: image build and push

## Required service account

Create a dedicated service account for the job, for example:

- `vertex-inventory-job@<PROJECT>.iam.gserviceaccount.com`

This service account should have:

### Bucket permissions

On the target bucket:

- `roles/storage.objectAdmin` for writing artifacts

### Resource read permissions

Grant the minimum read permissions required to inventory:

- Dialogflow CX agents
- Vertex reasoning engines
- IAM policies needed for offline binding computation
- service accounts if service-account inventory is included

Start broad only if needed, then reduce to least privilege.

## Configuration model

The job should support production config values like:

```json
{
  "flavor": "both",
  "fixtures": false,
  "bucketName": "my-inventory-bucket",
  "bucketPrefix": "vertex-inventory",
  "writeLatest": true,
  "output_dir": "/tmp/out"
}
```

Recommended meanings:

- `flavor`: `dialogflowcx`, `vertexai`, or `both`
- `fixtures`: `false` in production
- `bucketName`: destination bucket name
- `bucketPrefix`: top-level artifact prefix inside the bucket
- `writeLatest`: whether to maintain `latest/`
- `output_dir`: local temporary output path

## Local build and image push

Build and push the container image.

Example:

```bash
gcloud builds submit --tag gcr.io/<PROJECT>/vertex-tools-inventory:latest
```

If you use Artifact Registry instead, adjust the image name accordingly.

## Create the job service account

```bash
gcloud iam service-accounts create vertex-inventory-job \
  --display-name="Vertex Inventory Job"
```

## Grant bucket write access

```bash
gcloud storage buckets add-iam-policy-binding gs://<BUCKET> \
  --member="serviceAccount:vertex-inventory-job@<PROJECT>.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

## Create the Cloud Run Job

Example:

```bash
gcloud run jobs create vertex-tools-inventory \
  --image gcr.io/<PROJECT>/vertex-tools-inventory:latest \
  --region us-central1 \
  --service-account vertex-inventory-job@<PROJECT>.iam.gserviceaccount.com \
  --memory 1Gi \
  --cpu 1 \
  --set-env-vars INVENTORY_CONFIG_JSON='{"flavor":"both","fixtures":false,"bucketName":"<BUCKET>","bucketPrefix":"vertex-inventory","writeLatest":true,"output_dir":"/tmp/out"}'
```

If you prefer config from a mounted file or Secret Manager, that is also fine.

## Execute the job manually

```bash
gcloud run jobs execute vertex-tools-inventory --region us-central1
```

Use this before scheduling so you can verify the artifacts land in the bucket.

## Create the scheduler

Example hourly schedule:

```bash
gcloud scheduler jobs create http vertex-tools-inventory-hourly \
  --location us-central1 \
  --schedule "0 * * * *" \
  --uri "https://run.googleapis.com/v2/projects/<PROJECT>/locations/us-central1/jobs/vertex-tools-inventory:run" \
  --http-method POST \
  --oauth-service-account-email vertex-inventory-job@<PROJECT>.iam.gserviceaccount.com
```

Adjust the cron schedule to match the freshness you need.

## Suggested frequency

For governance use cases, one of these is usually enough:

- hourly
- every 6 hours
- daily

Choose the interval based on how fresh the inventory needs to be.

## Validation checklist

After a manual or scheduled run, verify:

1. the job completed successfully in Cloud Run Job execution logs
2. the run-specific GCS prefix exists
3. all four files exist in the run-specific prefix
4. the `latest/` prefix is updated if enabled
5. `manifest.json` reflects the run counts and warnings correctly

## Connector read pattern

The connector should read from a stable prefix such as:

```text
gs://<BUCKET>/<PREFIX>/latest/
```

The connector should not scan historical `runs/` prefixes.

## Operational recommendation

Keep the production flow:

- offline collection in the Cloud Run Job
- artifact storage in GCS
- connector ingestion from GCS

Avoid live IAM/resource collection in the connector by default, since that adds performance overhead and couples reconciliation to cloud API latency.

# GCP Permissions and Config Guide for Vertex Tools Inventory

This document complements `docs/gcp-deployment.md` and covers:

- the required GCP permissions and IAM roles for the inventory job service account
- example config JSON for fixture mode and live mode

## Job service account

Create a dedicated service account for the inventory job, for example:

- `vertex-inventory-job@<PROJECT>.iam.gserviceaccount.com`

Use this service account for the Cloud Run Job execution identity.

## Minimum GCP permissions and roles

The inventory job has two broad responsibilities:

1. **read inventory data** from Dialogflow CX, Vertex AI Agent Engine, IAM, and optionally IAM service accounts
2. **write generated artifacts** to GCS

## Required bucket role

On the destination bucket:

- `roles/storage.objectAdmin`

This allows the job to write and overwrite artifact files under the configured prefixes.

Example:

```bash
gcloud storage buckets add-iam-policy-binding gs://<BUCKET> \
  --member="serviceAccount:vertex-inventory-job@<PROJECT>.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

## Resource read roles

The exact least-privilege set depends on how the live collectors are implemented. The job needs enough permissions to:

- list Dialogflow CX agents
- list Vertex reasoning engines
- call `getIamPolicy` where resource-level IAM is supported
- read project-level IAM when project fallback is used
- optionally read IAM service account metadata if service-account enrichment is included

A practical initial setup is:

- a read role for Dialogflow CX resources
- a read role for Vertex AI resources
- an IAM read capability sufficient for `getIamPolicy`
- optional service account read capability

If you need to start broader and tighten later, document that explicitly and then reduce to least privilege after validating which permissions are actually used.

## Suggested permission categories

### Dialogflow CX inventory

The service account must be able to:

- list agents
- read agent metadata
- read tools, webhooks, and data store references if those are collected
- call `getIamPolicy` on the agent resource if resource-level IAM is used

### Vertex AI Agent Engine inventory

The service account must be able to:

- list reasoning engines
- read reasoning engine metadata
- read deployment service account metadata if exposed via the agent object
- call `getIamPolicy` on the reasoning engine resource if supported

### Project IAM fallback

The service account must be able to:

- read project IAM policy

This is required for the offline binding logic when project-level fallback is used.

### Service account inventory and enrichment

If the job also inventories runtime service accounts or enriches them later, it must be able to:

- read service account metadata
- optionally read service account IAM policy if service-account-related bindings are added later

## Operational recommendation

Use a dedicated job service account instead of reusing a broad admin identity. This makes it easier to:

- audit job access
- reduce permissions over time
- separate collector permissions from connector permissions

## Example role assignment flow

### Create the job service account

```bash
gcloud iam service-accounts create vertex-inventory-job \
  --display-name="Vertex Inventory Job"
```

### Grant bucket access

```bash
gcloud storage buckets add-iam-policy-binding gs://<BUCKET> \
  --member="serviceAccount:vertex-inventory-job@<PROJECT>.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

### Grant inventory read access

Grant the minimum read access your live collectors require for:

- Dialogflow CX
- Vertex AI
- project IAM
- optional service account metadata

Validate the permissions with a manual job execution before enabling the scheduler.

## Config JSON examples

The examples below are intended to show the shape of the job config.

## Fixture mode example

Use fixture mode for local development, CI, and schema validation.

```json
{
  "flavor": "both",
  "fixtures": true,
  "output_dir": "./out",
  "dialogflow_fixture_path": "tests/fixtures/dialogflow_agent.json",
  "vertex_fixture_path": "tests/fixtures/reasoning_engine.json",
  "iam_fixture_path": "tests/fixtures/iam_policies.json",
  "bucketName": "my-inventory-bucket",
  "bucketPrefix": "vertex-inventory",
  "writeLatest": true
}
```

Notes:

- `fixtures` is `true`
- fixture files are used instead of live GCP API calls
- `output_dir` can be local
- `bucketName`, `bucketPrefix`, and `writeLatest` can still be present if you want to test the upload path

## Live mode example

Use live mode in production.

```json
{
  "flavor": "both",
  "fixtures": false,
  "output_dir": "/tmp/out",
  "bucketName": "my-inventory-bucket",
  "bucketPrefix": "vertex-inventory",
  "writeLatest": true,
  "projectIds": [
    "demo-proj"
  ],
  "locations": [
    "us-central1"
  ]
}
```

Notes:

- `fixtures` is `false`
- live collectors should read GCP resources directly
- `/tmp/out` is a good default local output directory for Cloud Run Jobs
- `projectIds` and `locations` are examples of production-oriented scope inputs if the live collectors support them

## Minimal live mode example

If the collectors derive scope from environment or a smaller config, you can keep it simpler:

```json
{
  "flavor": "both",
  "fixtures": false,
  "output_dir": "/tmp/out",
  "bucketName": "my-inventory-bucket",
  "bucketPrefix": "vertex-inventory",
  "writeLatest": true
}
```

## Recommended config handling in GCP

For production, prefer:

- non-secret config in environment variables or a mounted config file
- secrets in Secret Manager

Examples of what should be non-secret:

- `flavor`
- `bucketName`
- `bucketPrefix`
- `writeLatest`
- project or location scope

If any future collector needs sensitive values, store them in Secret Manager rather than embedding them in the config JSON.

## Validation checklist

Before enabling the scheduler, verify that the job service account can:

1. read the target Dialogflow CX resources
2. read the target Vertex AI resources
3. read project IAM when fallback is required
4. write all four artifacts to the configured GCS prefix
5. update the `latest/` prefix if enabled

## Summary

The production split should remain:

- **Cloud Run Job service account**: reads cloud inventory data and writes artifacts to GCS
- **connector**: reads precomputed artifacts from GCS

Keep the connector out of the real-time collection path by default to avoid performance overhead during reconciliation.

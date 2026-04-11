# Vertex Tools Inventory

This repository generates a normalized, offline inventory for Vertex AI Agent Engine and Dialogflow CX assets. The job emits four JSON artifacts designed for downstream ingestion:

- `agents.json`
- `identity-bindings.json`
- `service-accounts.json`
- `manifest.json`

## How inventory is gathered

The entrypoint (`main.py`) loads an `InventoryConfig`, collects agents for the selected flavor, optionally collects IAM policies, normalizes everything, and writes all artifacts.

### Collection flow

1. **Select source flavor**: `dialogflowcx`, `vertexai`, or `both`.
2. **Collect agents from fixtures**:
   - Dialogflow CX collectors read `agents` from the Dialogflow fixture.
   - Vertex collectors read `reasoning_engines` from the Vertex fixture.
3. **Collect IAM policies (fixture mode)**:
   - Resource-level IAM policies are read from `resource_iam_policies`.
   - Project-level IAM policies are read from `project_iam_policies`.
4. **Normalize identities and relationships**:
   - Agent records are transformed into a shared normalized schema.
   - Identity bindings are generated from IAM with resource-first then project-fallback logic.
   - Runtime service accounts are extracted and deduplicated.
5. **Write artifacts**:
   - JSON files are written to `output_dir`.
   - `manifest.json` includes counts, scan metadata, and warnings.

## Design and logic

### Normalization goals

- Unify Dialogflow CX and Vertex Agent Engine into one agent schema.
- Keep identity-binding semantics consistent across flavors.
- Preserve provenance (`sourceTag`, confidence, scope) so downstream systems can reason about trust and inheritance.
- Keep v1 deterministic and offline-friendly (fixture-first).

### Identity-binding logic

Identity bindings are created per-agent using this precedence:

1. **Direct resource IAM** (`DIRECT_RESOURCE_BINDING`, `HIGH` confidence)
2. **Inherited project IAM fallback** (`INHERITED_PROJECT_BINDING`, `MEDIUM` confidence)
3. **Group member handling** marks bindings as `UNEXPANDED_GROUP` and `expanded=false`

Additional rules:

- Only IAM roles mapping to caller access are included (`invoke` or `manage`).
- Role normalization maps concrete IAM roles into normalized permissions (`invoke`, `read`, `manage`).
- Runtime identity self-bindings are excluded to avoid circular/noise entries.
- Binding IDs are deterministic hashes of `(agent, member, role, scope resource)`.

### Service-account logic

- Runtime identities are normalized to `serviceAccount:<email>` shape.
- Service accounts are deduplicated by `projects/<projectId>/serviceAccounts/<email>`.
- `linkedAgentIds` accumulates all agents using the same runtime identity.

---

## Artifact schemas

> Types below use: `string`, `boolean`, and `string[]`.

### `agents.json`

Array of normalized agent objects.

| Field | Type | Description |
|---|---|---|
| `id` | `string` | Stable normalized agent ID (`agent_id` or `engine_id` from source). |
| `platform` | `string` | Constant platform identifier (`GOOGLE_VERTEX_AI`). |
| `flavor` | `string` | Source flavor: `dialogflowcx` or `vertexai`. |
| `projectId` | `string` | GCP project ID containing the agent. |
| `location` | `string` | Region/location of the agent resource. |
| `displayName` | `string` | Human-readable agent/engine name. |
| `resourceName` | `string` | Full resource name for the agent/engine. |
| `sourceType` | `string` | Source classifier (for example `dialogflowcx_agent`, `vertex_reasoning_engine`). |
| `runtimeIdentity` | `string \| null` | Runtime principal used by the agent (usually service account). |
| `toolIds` | `string[]` | Tool IDs linked to the agent (empty in v1). |
| `knowledgeBaseIds` | `string[]` | Knowledge base IDs linked to the agent (empty in v1). |
| `guardrailId` | `string \| null` | Guardrail identifier if available (null in v1). |

### `identity-bindings.json`

Array of normalized caller-access bindings derived from IAM.

| Field | Type | Description |
|---|---|---|
| `id` | `string` | Deterministic binding ID (`ib-<hash>`). |
| `agentId` | `string` | ID of the related agent in `agents.json`. |
| `agentVersion` | `string` | Agent version marker (`latest` in v1). |
| `principal` | `string` | Normalized principal value (email/domain/public token). |
| `principalType` | `string` | Principal category (`USER`, `GROUP`, `SERVICE_ACCOUNT`, `DOMAIN`, etc.). |
| `iamMember` | `string` | Original IAM member string (`user:...`, `group:...`, etc.). |
| `iamRole` | `string` | Source IAM role. |
| `permissions` | `string[]` | Normalized permissions from role mapping (`invoke`, `read`, `manage`). |
| `scope` | `string` | Binding scope (`resource` or `project`). |
| `scopeType` | `string` | Scope enum (`AGENT_RESOURCE` or `PROJECT`). |
| `scopeResourceName` | `string` | Resource name where binding applies. |
| `sourceTag` | `string` | Provenance tag (`DIRECT_RESOURCE_BINDING`, `INHERITED_PROJECT_BINDING`, `UNEXPANDED_GROUP`). |
| `confidence` | `string` | Confidence score (`HIGH` for resource, `MEDIUM` for project fallback). |
| `kind` | `string` | Same value as `principalType` for downstream compatibility. |
| `flavor` | `string` | Agent flavor: `dialogflowcx` or `vertexai`. |
| `expanded` | `boolean` | `false` when group expansion was not performed; otherwise `true`. |

### `service-accounts.json`

Array of deduplicated runtime service accounts discovered from agents.

| Field | Type | Description |
|---|---|---|
| `id` | `string` | Canonical service-account resource key: `projects/<projectId>/serviceAccounts/<email>`. |
| `platform` | `string` | Constant platform identifier (`GOOGLE_VERTEX_AI`). |
| `email` | `string` | Service-account email. |
| `projectId` | `string` | Project ID associated with the service account record. |
| `linkedAgentIds` | `string[]` | Agent IDs using this runtime identity. |

### `manifest.json`

Single JSON object describing run metadata, counts, and generated files.

| Field | Type | Description |
|---|---|---|
| `generatedAt` | `string` | UTC timestamp when artifacts were written (RFC3339-like `YYYY-MM-DDTHH:MM:SSZ`). |
| `schemaVersion` | `string` | Manifest schema version (`1.0`). |
| `platform` | `string` | Platform constant (`GOOGLE_VERTEX_AI`). |
| `collectionMode` | `string` | Collection mode (`fixtures` or `live`). |
| `flavorsIncluded` | `string[]` | Distinct flavors found in the run. |
| `projectIdsScanned` | `string[]` | Distinct project IDs represented in collected agents. |
| `locationsScanned` | `string[]` | Distinct locations represented in collected agents. |
| `agentCount` | `number` | Number of records in `agents.json`. |
| `identityBindingCount` | `number` | Number of records in `identity-bindings.json`. |
| `serviceAccountCount` | `number` | Number of records in `service-accounts.json`. |
| `artifacts` | `object` | File + count map for each artifact (`agents`, `identityBindings`, `serviceAccounts`). |
| `warnings` | `string[]` | Warning messages generated from run conditions. |

### Manifest warning conditions

Warnings are emitted when:

- No identity bindings are generated.
- Project-level fallback was used for one or more bindings.
- One or more bindings are unexpanded groups.

## Run as a Cloud Run Job container

A minimal container image is included via `Dockerfile`. The default container command is:

```bash
python3 main.py --config /app/config/job-config.json
```

### Build locally

```bash
docker build -t vertex-tools-inventory:local .
```

### Run locally

```bash
docker run --rm \
  -v "$(pwd)/config/job-config.json:/app/config/job-config.json:ro" \
  -v "$(pwd)/out:/tmp/out" \
  -e GOOGLE_CLOUD_PROJECT="your-project-id" \
  vertex-tools-inventory:local
```

### Required config / environment

- Provide a config file at `/app/config/job-config.json` (mount one in, or bake one in the image).
- For live collection, set `projectIds` in config (or set `GOOGLE_CLOUD_PROJECT` for fallback when omitted).
- If writing to GCS (`bucketName` set in config), authenticate with GCP credentials available to the container runtime.

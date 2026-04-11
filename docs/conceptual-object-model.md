# Conceptual Object Model for Provider-Based Agent Governance Crawlers

## Purpose

This document defines a **conceptual object model** for the provider-based crawler architecture.

It describes the major object types the crawler discovers or derives, and the relationships between:
- the **Agent**
- invocation boundaries such as **Alias** or **Deployment**
- **Tools**
- **Guardrails**
- **Knowledge Bases (KBs)**
- **Memory**
- **Keys / Credentials**
- **Identity Bindings**
- **Runtime Identities**
- **Activity Log**

This is a platform-neutral model intended to work across providers such as Vertex, Bedrock, Foundry, and future platforms.

---

# 1. Design goals

The model is intended to support these questions:

1. What agents exist?
2. What can each agent use or connect to?
3. Under what identity does the agent run?
4. Who can access the agent?
5. Why can they access it?
6. What credentials or keys are involved?
7. What governance controls are attached?
8. What activity has the agent performed?

The model is conceptual, not tied to a specific storage engine, but it maps naturally to a node-and-edge representation in Elasticsearch.

---

# 2. Core object types

## 2.1 Agent

The central governed object.

An **Agent** represents the logical AI actor that is exposed to users, workloads, or applications.

Typical attributes:
- `id`
- `provider`
- `platform`
- `resourceId`
- `displayName`
- `agentType`
- `region` / `location`
- `tenantId` / `accountId` / `projectId`
- `status`
- `runtimeIdentity`
- `createdAt`
- `updatedAt`

Examples:
- Vertex reasoning engine
- Dialogflow agent
- Bedrock agent
- Foundry agent

---

## 2.2 Invocation Boundary

Some platforms do not expose the agent itself as the real invocation surface.

An **Invocation Boundary** represents the actual callable surface.

Subtypes can include:
- `AgentAlias`
- `Deployment`
- `Endpoint`
- `Version`
- `WorkspaceScopedAgentView`

Typical attributes:
- `id`
- `resourceId`
- `boundaryType`
- `displayName`
- `status`
- `routingConfiguration`
- `createdAt`
- `updatedAt`

This object exists because access is often granted to:
- an alias
- a deployment
- an endpoint
- a versioned callable surface
rather than directly to the agent object.

---

## 2.3 Tool

A **Tool** is an external capability an agent can invoke.

Examples:
- OpenAPI action
- MCP tool
- search connector
- code interpreter
- connected agent
- function/action group

Typical attributes:
- `id`
- `toolType`
- `name`
- `description`
- `providerSpecificConfig`
- `connectionRef`
- `authType`
- `source`

A Tool may itself depend on:
- credentials
- connections
- KBs
- memory stores

---

## 2.4 Guardrail

A **Guardrail** is a control object that constrains or filters agent behavior.

Examples:
- content safety policy
- prompt filtering policy
- RAI configuration
- policy pack

Typical attributes:
- `id`
- `name`
- `guardrailType`
- `status`
- `policyRef`
- `providerSpecificConfig`

---

## 2.5 Knowledge Base

A **Knowledge Base** is a data source or retrieval configuration used by the agent.

Examples:
- retrieval corpus
- vector store binding
- Azure knowledge base reference
- search index
- document collection

Typical attributes:
- `id`
- `name`
- `kbType`
- `backingStoreType`
- `connectionRef`
- `indexRef`
- `providerSpecificConfig`

---

## 2.6 Memory

A **Memory** object represents persistent or semi-persistent conversational or agent context.

Examples:
- conversation memory store
- thread state
- session memory
- retrieval memory

Typical attributes:
- `id`
- `memoryType`
- `storageType`
- `retentionPolicy`
- `providerSpecificConfig`

Not every platform exposes Memory explicitly. Some providers may infer it from tool or runtime configuration.

---

## 2.7 Key / Credential

A **Key / Credential** is a governed secret or non-human authentication material used by the agent or one of its connected artifacts.

Examples:
- API key
- secret reference
- OAuth client credential
- cloud access key
- connection secret
- signing key
- certificate

Typical attributes:
- `id`
- `credentialType`
- `name`
- `secretRef`
- `rotationState`
- `expirationState`
- `providerSpecificConfig`

Important: the object model should represent the credential relationship even when the secret value itself is never collected.

---

## 2.8 Runtime Identity

A **Runtime Identity** is the identity the agent executes as when calling downstream systems.

Examples:
- GCP service account
- AWS role
- Azure managed identity
- service principal

Typical attributes:
- `id`
- `identityType`
- `principalValue`
- `accountId` / `tenantId` / `projectId`
- `status`

This object is distinct from caller access.

---

## 2.9 Principal

A **Principal** is a subject that may be granted access to an agent.

Examples:
- user
- group
- role
- service account
- service principal
- workload identity

Typical attributes:
- `id`
- `principalType`
- `principalValue`
- `displayName`
- `provider`
- `accountId` / `tenantId` / `projectId`

---

## 2.10 Identity Binding

An **Identity Binding** is the normalized access relationship that answers:

> This principal can access this agent or invocation boundary at this scope, for this reason.

Typical attributes:
- `id`
- `principalRef`
- `targetRef`
- `permissions`
- `scopeType`
- `scopeResourceName`
- `bindingOrigin`
- `sourceTag`
- `conditionJson`
- `confidence`
- `expanded`
- `rawRole` / `rawPolicyRef`

Identity Binding is usually a derived object computed by the crawler from raw platform policies or role assignments.

---

## 2.11 Activity Log Event

An **Activity Log Event** represents observed activity involving the agent or one of its related objects.

Examples:
- invoke event
- tool call event
- KB query
- memory update
- policy evaluation
- secret use
- access change

Typical attributes:
- `id`
- `eventType`
- `timestamp`
- `actorRef`
- `targetRef`
- `outcome`
- `context`

The activity log is not only for usage analytics. It is a governance object because it helps answer:
- what the agent did
- what it accessed
- which tool or KB was used
- whether a sensitive credential was involved

---

# 3. Relationship model

Below is the conceptual relationship model.

```text
Principal
   |
   | CAN_ACCESS (IdentityBinding)
   v
Invocation Boundary ---- REPRESENTS ----> Agent
                                   |
                                   | EXECUTES_AS
                                   v
                             Runtime Identity
                                   |
                                   | USES
                                   v
                             Key / Credential

Agent ---- USES ----> Tool
Agent ---- USES ----> Knowledge Base
Agent ---- USES ----> Memory
Agent ---- PROTECTED_BY ----> Guardrail
Agent ---- EMITS / HAS ----> Activity Log Event

Tool ---- USES ----> Key / Credential
Tool ---- READS ----> Knowledge Base
Tool ---- READS_WRITES ----> Memory
Knowledge Base ---- USES ----> Key / Credential
Memory ---- USES ----> Key / Credential
```

This is the conceptual heart of the model.

---

# 4. Primary relationships explained

## 4.1 Invocation Boundary REPRESENTS Agent

Reason:
Many platforms do not grant access directly to the agent object.
Instead, access may be granted to:
- an alias
- a deployment
- an endpoint
- a versioned callable surface

So the model distinguishes:
- **logical governed object** = Agent
- **actual invocation surface** = Invocation Boundary

Relationship:
- `InvocationBoundary REPRESENTS Agent`

---

## 4.2 Principal CAN_ACCESS Agent / Invocation Boundary via Identity Binding

Reason:
Access is rarely stored as a simple list of users on the agent.
It is usually derived from:
- IAM policies
- RBAC role assignments
- group inheritance
- project/workspace/account-level scope

Relationship:
- `Principal --CAN_ACCESS--> InvocationBoundary` or `Agent`

The **Identity Binding** records:
- who
- what target
- what scope
- why
- with what confidence

---

## 4.3 Agent EXECUTES_AS Runtime Identity

Reason:
The identity the agent runs as is not the same as the principals who may invoke it.

Relationship:
- `Agent --EXECUTES_AS--> RuntimeIdentity`

Examples:
- a Vertex reasoning engine runs as a service account
- a Bedrock agent may operate through an AWS role
- a Foundry agent may rely on a managed identity

---

## 4.4 Runtime Identity USES Key / Credential

Reason:
The runtime identity may authenticate into downstream systems using:
- API keys
- connection secrets
- OAuth clients
- certificates
- cloud credentials

Relationship:
- `RuntimeIdentity --USES--> KeyCredential`

This is one place where secret governance intersects agent governance.

---

## 4.5 Agent USES Tool

Reason:
Tools are one of the most important agent relationships because they show:
- what the agent can do
- what downstream systems it can affect

Relationship:
- `Agent --USES--> Tool`

Tools may also connect to other governed objects.

---

## 4.6 Agent USES Knowledge Base

Reason:
Knowledge sources are central to agent behavior and data exposure.

Relationship:
- `Agent --USES--> KnowledgeBase`

This relationship tells you:
- what the agent can retrieve
- what data it can ground responses in
- what data stores matter for governance

---

## 4.7 Agent USES Memory

Reason:
Memory changes what the agent can retain and how context persists over time.

Relationship:
- `Agent --USES--> Memory`

This matters for:
- privacy
- retention
- cross-session state
- behavioral drift

---

## 4.8 Agent PROTECTED_BY Guardrail

Reason:
Guardrails are governance controls.

Relationship:
- `Agent --PROTECTED_BY--> Guardrail`

This tells you whether the agent has:
- safety constraints
- policy constraints
- filtering or moderation controls

---

## 4.9 Tool / KB / Memory USES Key / Credential

Reason:
An agent may not hold the credential directly.
The credential may be attached to:
- a connection used by a tool
- a KB backend connector
- a memory store connector

Relationships:
- `Tool --USES--> KeyCredential`
- `KnowledgeBase --USES--> KeyCredential`
- `Memory --USES--> KeyCredential`

This lets you trace secret usage through the graph.

---

## 4.10 Agent HAS / EMITS Activity Log Event

Reason:
The crawler may collect or later ingest activity logs to show what happened in practice.

Relationship:
- `ActivityLogEvent --TARGETS--> Agent`
- optionally `ActivityLogEvent --USES--> Tool`
- optionally `ActivityLogEvent --READS--> KnowledgeBase`
- optionally `ActivityLogEvent --WRITES--> Memory`

This relationship supports:
- explainability
- forensics
- usage analytics
- policy validation

---

# 5. Recommended object hierarchy

A useful way to think about the model is by layers.

## Layer 1: Primary governed objects
- Agent
- Invocation Boundary
- Principal
- Runtime Identity

## Layer 2: Capability and data artifacts
- Tool
- Knowledge Base
- Memory
- Guardrail

## Layer 3: Secret and auth artifacts
- Key / Credential

## Layer 4: Derived and observational artifacts
- Identity Binding
- Activity Log Event

This layering helps developers understand what to crawl first and what can be derived later.

---

# 6. Example graph traversals

## 6.1 Who can access this agent?

Traversal:
- `Agent <- InvocationBoundary <- IdentityBinding <- Principal`

or directly:
- `Agent <- IdentityBinding <- Principal`

## 6.2 Which credentials can this agent indirectly use?

Traversal:
- `Agent -> RuntimeIdentity -> KeyCredential`
- `Agent -> Tool -> KeyCredential`
- `Agent -> KnowledgeBase -> KeyCredential`
- `Agent -> Memory -> KeyCredential`

## 6.3 Which KBs and tools are associated with a risky principal?

Traversal:
- `Principal -> IdentityBinding -> Agent -> Tool`
- `Principal -> IdentityBinding -> Agent -> KnowledgeBase`

## 6.4 Which activity events involved memory or secret use?

Traversal:
- `ActivityLogEvent -> Agent`
- `ActivityLogEvent -> Tool -> KeyCredential`
- `ActivityLogEvent -> Memory`

---

# 7. What the crawler should collect directly vs derive

## Collect directly where possible
- Agent
- Invocation Boundary
- Tool
- Guardrail
- Knowledge Base
- Memory
- Runtime Identity
- Principal
- raw activity events
- raw role / policy / assignment facts

## Derive in the crawler or normalization layer
- Identity Binding
- confidence
- sourceTag
- bindingOrigin
- cross-object relationship edges
- stale / inactive lifecycle state

This separation is important.
The crawler should not depend on one provider exposing an already-normalized access object.

---

# 8. Recommended minimal v1 object set

If a new platform is being implemented and the developer wants the minimum viable graph, start with:

- Agent
- Invocation Boundary (if needed)
- Principal
- Identity Binding
- Runtime Identity
- Tool
- Knowledge Base
- Guardrail

Then add:
- Memory
- Key / Credential
- Activity Log

That gives a practical phased rollout.

---

# 9. Developer guidance for the next provider

When implementing the next provider, map its native objects into this model using the following steps.

## Step 1: identify the logical agent object
Map that to **Agent**.

## Step 2: identify the true callable surface
If distinct, map that to **Invocation Boundary**.

## Step 3: identify who may call it
Map those subjects to **Principal** and compute **Identity Binding**.

## Step 4: identify execution identity
Map that to **Runtime Identity**.

## Step 5: inventory capability artifacts
Map external action surfaces to **Tool**.

## Step 6: inventory data artifacts
Map retrieval or grounding sources to **Knowledge Base**.
Map session/context stores to **Memory**.

## Step 7: inventory controls
Map policy/safety constraints to **Guardrail**.

## Step 8: inventory secrets and credentials
Model credentials even if only secret references are available.

## Step 9: ingest activity if available
Map execution / usage events into **Activity Log Event** objects.

---

# 10. Final recommendation

The conceptual center of the model is:

- **Agent** as the governed AI object
- **Invocation Boundary** as the real callable surface when needed
- **Identity Binding** as the derived answer to who can access the agent
- **Runtime Identity** as the answer to what identity the agent acts as
- **Tool / KB / Memory / Guardrail / Credential** as the major related artifacts
- **Activity Log** as the observed behavior layer

This model is broad enough to support Vertex, Bedrock, Foundry, and future providers while remaining concrete enough for developers to implement consistently.

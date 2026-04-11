# Offline Vertex Inventory Job

## Goal
Build one offline inventory job that supports both Dialogflow CX and Vertex Agent Engine and emits normalized inventory artifacts for downstream connector ingestion.

## Flavors
- dialogflowcx
- vertexai

## Output artifacts
- agents.json
- identity-bindings.json
- service-accounts.json
- manifest.json

## Non-goals for v1
- no group expansion
- no write operations
- no UI
- no connector code in this repo

## Binding precedence
1. direct resource IAM
2. fallback project IAM
3. service-account IAM as a separate relation

## Normalized permissions
- invoke
- read
- manage

## Required identity binding fields
- id
- agentId
- agentVersion
- principal
- principalType
- iamMember
- iamRole
- permissions
- scope
- scopeType
- scopeResourceName
- sourceTag
- confidence
- kind
- flavor
- expanded

## Source tags
- DIRECT_RESOURCE_BINDING
- INHERITED_PROJECT_BINDING
- SERVICE_ACCOUNT_BINDING
- UNEXPANDED_GROUP
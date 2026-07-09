# Phase 3.5 — Implementation Blueprint & Engineering Mapping

**Version:** 1.0  
**Author:** Sahil — Lead Architect  
**Status:** Pre-Implementation Engineering Blueprint  
**Review Board:** Google, Microsoft, Amazon, OpenAI, Anthropic, NVIDIA principal architects  
**Phase Readiness Target:** 9.8/10

---

## Table of Contents

1. [Package Ownership Matrix](#1-package-ownership-matrix)
2. [Layer Mapping](#2-layer-mapping)
3. [Aggregate Implementation Matrix](#3-aggregate-implementation-matrix)
4. [Command Handler Mapping](#4-command-handler-mapping)
5. [Query Handler Mapping](#5-query-handler-mapping)
6. [Event Processing Matrix](#6-event-processing-matrix)
7. [API Ownership Matrix](#7-api-ownership-matrix)
8. [Background Job Mapping](#8-background-job-mapping)
9. [Redis Blueprint](#9-redis-blueprint)
10. [Database Ownership Matrix](#10-database-ownership-matrix)
11. [Folder Ownership](#11-folder-ownership)
12. [Dependency Rules](#12-dependency-rules)
13. [Engineering Standards](#13-engineering-standards)
14. [Implementation Order](#14-implementation-order)
15. [Team Responsibility Matrix](#15-team-responsibility-matrix)
16. [Risk Before Coding](#16-risk-before-coding)
17. [Coding Readiness Checklist](#17-coding-readiness-checklist)
18. [Engineering Review](#18-engineering-review)

---


# 1. Package Ownership Matrix

| Package | Purpose | Responsibilities | Allowed Dependencies | Forbidden Dependencies | Owner Layer | Extraction Strategy |
|---|---|---|---|---|---|---|
| api/ | Routes, middleware, request/response models | Define HTTP endpoints, validate input, serialize responses, apply middleware, handle errors | application/, config/, middleware/ | domain/, infrastructure/, agents/, tools/ | Interface Adapters | Extract into standalone API gateway package |
| application/ | Application services, command handlers, query handlers, event handlers, DTOs, mappers | Orchestrate use cases, dispatch commands/queries, map domain to DTOs, publish events | domain/, services/, config/ | infrastructure/, api/, agents/, tools/ | Application | Extract into application bus package with CQRS |
| domain/ | Aggregates, entities, value objects, domain services, domain events, specifications, policies, invariants, repository interfaces | Enforce business invariants, model rich domain logic, define repository contracts, emit domain events | None (zero external deps) | infrastructure/, api/, config/, agents/, tools/ | Domain | Extract into shared domain library (nuget/pypi) |
| infrastructure/ | Database, Redis, Celery, LLM clients, vector search, monitoring, health checks | Implement persistence, messaging, AI provider clients, observability tooling | config/, domain/ (interfaces only) | api/, application/, agents/, tools/ | Infrastructure | Split into provider-specific packages (infra-db, infra-queue, infra-ai) |
| repositories/ | Repository implementations (one per aggregate) | Implement domain repository interfaces with ORM, manage unit-of-work, handle transactions | domain/, infrastructure/ (db session) | api/, application/, agents/, tools/ | Infrastructure | Extract per-aggregate into separate packages |
| services/ | Application-level business services, not in domain | Compose domain objects, coordinate cross-aggregate flows, implement use-case logic | domain/, application/ (events) | infrastructure/, api/, agents/ | Application | Merge into application/ package |
| agents/ | LangGraph agent definitions, graph state, node functions | Define agent topologies, state machines, node transitions, tool-calling logic | domain/, services/, tools/, memory/, rag/, config/ | infrastructure/, api/, repositories/ | Agent Layer | Extract into agents-runtime package |
| memory/ | Short-term (conversation buffer), long-term (PostgreSQL), semantic (vector) | Manage conversation history, persist sessions, store/retrieve embeddings | config/, domain/ (interfaces) | api/, agents/, tools/ | Infrastructure | Split into memory-shortterm, memory-longterm, memory-semantic packages |
| rag/ | Embedding, retrieval, context building, re-ranking | Generate embeddings, query vector store, build prompt context, re-rank results | config/, infrastructure/ (llm client, vector store) | api/, application/, domain/ | AI/ML Layer | Extract into rag-engine package |
| tools/ | Tool definitions, tool execution pipeline, tool registry | Define tool schemas, validate arguments, execute tool calls, manage registry | domain/, services/, config/ | infrastructure/, api/, agents/ | Agent Layer | Extract into tools-runtime package |
| workflows/ | n8n webhook integration, workflow orchestration | Trigger external workflows, receive webhook callbacks, map workflow state to domain events | config/, infrastructure/ (http client) | domain/, application/, agents/ | Integration Layer | Extract into workflow-bridge package |
| tasks/ | Celery task definitions per worker | Define async task functions, manage task routing, handle retries/dead-letter | application/, services/, infrastructure/ | api/, agents/, domain/ | Infrastructure | Extract into tasks-worker package |
| monitoring/ | Prometheus metrics, health checks, structured logging, tracing | Collect metrics, expose /health and /metrics endpoints, emit structured logs, propagate trace context | config/ | domain/, application/, agents/ | Infrastructure | Extract into observability-sdk package |
| middleware/ | Auth, identity, rate limiting, request ID, error handling | Authenticate requests, authorize actions, enforce rate limits, attach request IDs, normalize errors | config/, services/ (identity) | domain/, infrastructure/, agents/ | Interface Adapters | Extract into middleware-gateway package |
| config/ | Settings, env loading, feature flags, prompt registry | Load env vars, validate config, expose typed settings, manage prompt templates | None (zero external deps) | domain/, infrastructure/, api/ | Foundation | Extract into config-center package |
| prompts/ | Prompt templates, versioning, registry | Store/manage prompt templates, version prompts, substitute variables | config/ | domain/, infrastructure/, api/ | AI/ML Layer | Extract into prompt-manager package |
| tests/ | Unit, integration, e2e, fixtures, factories | Mock dependencies, spin up test containers, generate test data, assert behavior | All packages (test deps only) | Production code paths | Quality | Extract into test-utils package |


## 2. Layer Mapping

Establishes the canonical mapping between every DDD tactical pattern and the concrete implementation layer it occupies. Each component type has a single owner layer; all cross-layer calls follow strict dependency inversion.

    ┌─────────────────────────────────────────────────────────────────────────┐
    │  API Layer                                                             │
    │  FastAPI routes, middleware, request/response models, OpenAPI schema   │
    ├─────────────────────────────────────────────────────────────────────────┤
    │  Application Layer                                                     │
    │  Services, command handlers, query handlers, event handlers, DTOs      │
    ├─────────────────────────────────────────────────────────────────────────┤
    │  Domain Layer                                                          │
    │  Aggregates, entities, value objects, domain services, events,         │
    │  specifications, policies, invariants                                  │
    ├─────────────────────────────────────────────────────────────────────────┤
    │  Infrastructure Layer                                                  │
    │  Repositories (impl), DB, Redis, Celery, LLM, vector search, monitoring│
    └─────────────────────────────────────────────────────────────────────────┘
    │                                                                        │
    └── Dependencies point inward — outer layers depend on inner layers      │
       Infrastructure implements Domain interfaces; no layer                  │
       depends on outer layers.                                              │

The table below maps each DDD component onto its layer stack. Every arrow represents a dependency or data flow at runtime.

### Aggregate

    Aggregate → Application Service → Repository → Database → Events → API
    Domain     Application           Infra          Infra     Domain    API

    Caption: The Aggregate lives in the Domain Layer and is loaded by an Application
    Service that calls a Repository interface (Domain). The Infrastructure implements
    the Repository to fetch/store from the Database. Side-effect Domain Events are
    published after persistence and may be projected back through the API via
    response DTOs or WebSocket push.

### Command

    Command → Command Handler → Application Service → Repository → Events
    API      Application        Application          Infra        Domain

         ↘ Celery → Saga Coordinator
           Infra     Application

    Caption: The Command is a Pydantic model received at the API Layer, validated by
    middleware, and forwarded to a Command Handler in the Application Layer. The
    handler invokes an Application Service (write model), which calls a Repository
    to persist. Domain Events produced are dispatched through Celery to drive a Saga
    Coordinator for long-running transactions.

### Query

    Query → Query Handler → Read Model → Cache → Database → API
    API    Application      Application   Infra   Infra     API

    Caption: Queries bypass the Domain Layer entirely. A Query Handler receives a
    read request at the API boundary, checks the Redis cache (Infrastructure), and on
    a miss fetches from the read-optimized database projection. The result is
    serialized to a Read Model DTO and returned through the API.

### Domain Event

    Domain Event → Producer → Event Handler → Consumers → Queue → Celery
    Domain        Domain      Application      Domain/App   Infra   Infra

         ↘ Notification (email/push/Slack)
           Infra

    Caption: A Domain Event is raised within an Aggregate (Domain Layer). The
    Producer serializes it and publishes to a message queue (Infrastructure).
    Event Handlers in the Application Layer consume the event and fan out to
    registered Consumers (Domain or Application). Celery workers provide
    async delivery; side-effect notifications (email, Slack, push) run as
    Infrastructure adapters.

### Domain Service

    Domain Service
        ↑ calls
    Application Service  (caller)
        ↓ depends on
    Repository  (interface — Domain)

    Caption: A Domain Service encapsulates stateless domain logic that does not
    naturally fit on an Entity or Value Object. It is invoked by an Application
    Service but lives in the Domain Layer. Its dependencies (e.g. Repository
    interfaces) are injected via the constructor — the concrete implementations
    reside in Infrastructure.

### Specification

    Specification → Repository → Query/Filter → Database
    Domain         Domain        Infra           Infra

    Caption: A Specification is a domain predicate (e.g. "Orders older than 30
    days") defined as a Value Object in the Domain Layer. The Repository interface
    accepts a Specification and the Infrastructure implementation translates it
    into a database query (SQL WHERE, Redis SCAN, etc.). This keeps query logic
    expression in the domain while the execution mechanism stays in Infrastructure.

### Policy

    Policy → Policy Evaluator → Domain Service → Event
    Domain  Domain               Domain          Domain

    Caption: A Policy (Strategy pattern) lives in the Domain Layer and encapsulates
    business rules that execute conditionally. The Policy Evaluator selects and
    runs the matching policy, which may invoke a Domain Service and produce a
    Domain Event. No Application or Infrastructure dependency exists — policies are
    pure domain logic.

### Repository Interface → Implementation

    Repository interface  →  Infrastructure (impl)  →  Database / Redis
    Domain (port)            Infra (adapter)            Infra (detail)

    Caption: The Repository interface is defined in the Domain Layer as a port.
    The concrete implementation lives in Infrastructure as an adapter (Hexagonal
    Architecture). The mapping from domain entity to database rows is the
    responsibility of the Infrastructure adapter only. Application Services depend
    on the interface and are never coupled to a specific database technology.




# 3. Aggregate Implementation Matrix

Each aggregate is a consistency boundary. The table below maps every component — application service, repository, database table, Redis usage, events, Celery tasks, n8n workflows, APIs, and dependencies — to exactly one aggregate. This prevents cross-aggregate coupling and enforces the rule that a transaction touches only one aggregate.

---

## 3.1 Conversation Aggregate

Aggregate Root: Conversation (conversation_id)

| Column | Mappings | Rationale |
| --- | --- | --- |
| Aggregate Root | Conversation (conversation_id) | Central entity that owns all messages and state within a single chat session. |
| Application Service | ConversationService | Orchestrates append-message, create-conversation, archive-conversation use cases. |
| Repository | ConversationRepository | Loads/saves the full Conversation aggregate; never exposes child entities directly. |
| Database Tables | conversations, conversation_messages, conversation_participants | conversations is the root table; children are only accessed through it. |
| Redis Usage | Key: conversation:{id}:lock (distributed lock); Key: conversation:{id}:recent (last 50 messages, TTL 1h); Pub/Sub channel conversation:{id}:typing for real-time typing indicators. | Locks prevent concurrent append on the same conversation. Cached recent messages avoid DB round-trips on reconnect. Pub/Sub pushes typing events without polling. |
| Events Produced | ConversationCreated, MessageAppended, ConversationArchived, ParticipantAdded, ParticipantRemoved | Each event carries the conversation_id and a version number for optimistic concurrency. |
| Events Consumed | UserDisconnected (from UserProfile aggregate) — triggers ParticipantRemoved when a user leaves. | Ensures participant list stays consistent with active connections. |
| Celery Tasks | send_conversation_email_summary (periodic, daily digest of unread messages); expire_stale_conversations (archives conversations idle > 30 days). | Summary email is a background job with no strict timing requirement. Stale expiry is a scheduled maintenance task. |
| n8n Workflows | conversation_auto_reply (watches ConversationCreated webhook, replies with canned response if outside business hours); conversation_sentiment_log (watches MessageAppended webhook, writes sentiment score to Google Sheets for analytics). | Auto-reply and sentiment logging are external automations that do not need to live in the application process. |
| Public APIs | POST /api/v1/conversations, GET /api/v1/conversations/{id}, POST /api/v1/conversations/{id}/messages, DELETE /api/v1/conversations/{id} | REST endpoints that accept external traffic. All operations go through ConversationService. |
| Internal APIs | POST /internal/conversations/validate-participants (called by Meeting aggregate before adding conversation references); GET /internal/conversations/{id}/exists (called by Notification aggregate to verify target conversation is still active). | Internal endpoints bypass auth scopes and must never be exposed to the public gateway. |
| Dependencies | UserProfile aggregate (participant lookups), Notification aggregate (sending message-received push), Meeting aggregate (linking conversations to meetings). | Dependencies are expressed as events consumed or internal API calls — never as direct repository access. |

---

## 3.2 Meeting Aggregate

Aggregate Root: Meeting (meeting_id)

| Column | Mappings | Rationale |
| --- | --- | --- |
| Aggregate Root | Meeting (meeting_id) | Owns scheduling, state machine (scheduled/active/ended/cancelled), and participant roster. |
| Application Service | MeetingService | Handles schedule, join, leave, cancel, end-meeting, and generate-transcript. |
| Repository | MeetingRepository | Manages persistence for the Meeting aggregate; enforces that transcripts and recordings are only accessed via the Meeting. |
| Database Tables | meetings, meeting_participants, meeting_transcripts, meeting_recordings | meetings is the root. Child rows never have their own repository. |
| Redis Usage | Key: meeting:{id}:state (current state + participant count, TTL = meeting duration + 1h); Key: meeting:{id}:live-transcript (streaming transcript buffer, list data structure); Pub/Sub channel meeting:{id}:events for real-time participant join/leave. | In-memory state avoids DB writes on every participant event. Live transcript buffer is flushed to meeting_transcripts on end-meeting. Pub/Sub drives the real-time UI. |
| Events Produced | MeetingScheduled, MeetingStarted, MeetingEnded, MeetingCancelled, ParticipantJoined, ParticipantLeft, TranscriptReady | TranscriptReady is produced after the async transcription Celery task completes. |
| Events Consumed | UserProfileUpdated (re-fetches display name for participants); ConversationArchived (if a linked conversation is archived, logs a warning in meeting metadata). | Keeps meeting display names up to date without coupling to UserProfileRepository. |
| Celery Tasks | transcribe_meeting_recording (long-running, spawns a GPU worker for speech-to-text); generate_meeting_summary (runs LLM summarization on completed transcript); cleanup_orphan_recordings (periodic, removes recordings with no meeting reference > 7 days). | Transcription and summarization are CPU/GPU-heavy and must not block the request cycle. Orphan cleanup is a safety net. |
| n8n Workflows | meeting_calendar_sync (watches MeetingScheduled webhook, creates Google Calendar / Outlook event); meeting_recording_archive (watches MeetingEnded webhook, uploads recording to S3 and sends Slack notification). | Calendar sync and archival storage are external integrations best handled by n8n. |
| Public APIs | POST /api/v1/meetings, GET /api/v1/meetings/{id}, POST /api/v1/meetings/{id}/join, POST /api/v1/meetings/{id}/end, GET /api/v1/meetings/{id}/transcript | Full CRUD + action endpoints for meeting lifecycle. |
| Internal APIs | POST /internal/meetings/batch-status (called by Dashboard aggregate to show upcoming meetings); GET /internal/meetings/{id}/participant-count (called by Notification aggregate for capacity alerts). | Batch status endpoint avoids N+1 queries for dashboard. Participant count is used for real-time capacity warnings. |
| Dependencies | Conversation aggregate (meetings can have linked conversations), UserProfile aggregate (participant validation), KnowledgeDocument aggregate (meeting summary saved as knowledge document). | Transcripts flow into KnowledgeDocument as a write-after-complete side effect. |

---

## 3.3 Lead Aggregate

Aggregate Root: Lead (lead_id)

| Column | Mappings | Rationale |
| --- | --- | --- |
| Aggregate Root | Lead (lead_id) | Owns the lead lifecycle from capture to qualification, conversion, or discard. |
| Application Service | LeadService | Implements capture, qualify, assign, convert, merge, and discard operations. |
| Repository | LeadRepository | Persists lead records and scoring history. Enforces that interactions are only added through the Lead aggregate. |
| Database Tables | leads, lead_interactions, lead_scores, lead_assignments | leads is the root. Interactions and scores are value objects inside the aggregate boundary. |
| Redis Usage | Key: lead:{id}:lock (distributed lock on qualification to prevent double-scoring); Key: lead:score-queue (sorted set, score = lead score, used for prioritization); Key: lead:capture:dedup:{email_hash} (TTL 24h, prevents duplicate capture). | Dedup key avoids creating two leads from the same email within 24h. Score queue powers the "hot leads first" dashboard. |
| Events Produced | LeadCaptured, LeadQualified, LeadAssigned, LeadConverted, LeadMerged, LeadDiscarded | Each event carries the current score and owner ID so downstream consumers can act immediately. |
| Events Consumed | MeetingEnded (if lead was a meeting participant, auto-qualify based on meeting outcome); ConversationArchived (if lead had an active conversation, mark lead as stale). | Connects meeting and conversation outcomes back to lead scoring without coupling. |
| Celery Tasks | enrich_lead_with_enrichment_api (calls Clearbit/Hunter to fill company data); score_lead_batch (runs ML scoring model on newly captured leads every 5 minutes); 
otify_lead_assignment (sends email/Slack to assigned sales rep). | Enrichment and ML scoring are async because they call external APIs or models. Assignment notification is fire-and-forget. |
| n8n Workflows | lead_to_crm (watches LeadConverted webhook, pushes to Salesforce/HubSpot); lead_abandoned_followup (watches LeadDiscarded after 7 days, sends re-engagement email sequence). | CRM sync is an external integration. Follow-up sequences are marketing automations. |
| Public APIs | POST /api/v1/leads, GET /api/v1/leads/{id}, PATCH /api/v1/leads/{id}/qualify, POST /api/v1/leads/{id}/convert, GET /api/v1/leads (with filter/sort by score) | Capture comes from public-facing forms; qualify/convert are used by internal sales tools but exposed through the same API gateway with role-based access. |
| Internal APIs | POST /internal/leads/batch-import (CSV upload for sales ops); GET /internal/leads/score-distribution (called by analytics dashboard). | Batch import bypasses individual validation. Score distribution is a read-model endpoint. |
| Dependencies | UserProfile aggregate (assignment to sales rep), Notification aggregate (assignment alerts), KnowledgeDocument aggregate (lead enrichment results stored as documents). | Lead enrichment writes to KnowledgeDocument as a side effect. |

---

## 3.4 UserProfile Aggregate

Aggregate Root: UserProfile (user_id)

| Column | Mappings | Rationale |
| --- | --- | --- |
| Aggregate Root | UserProfile (user_id) | Owns identity, authentication metadata, preferences, and profile data. |
| Application Service | UserProfileService | Handles registration, profile update, preference change, password reset, and account deactivation. |
| Repository | UserProfileRepository | Persists profile and authentication data. Preferences are serialized as a JSON value object. |
| Database Tables | user_profiles, user_auth_tokens, user_preferences, user_login_history | user_profiles is the root. Auth tokens and login history are owned by the profile. |
| Redis Usage | Key: session:{token} (TTL = session lifetime, stores user_id + roles); Key: user:{id}:rate-limit:{endpoint} (sliding window counter, TTL = window); Key: user:{id}:online (flag updated by heartbeat, TTL 2 minutes). | Session cache eliminates DB lookup on every authenticated request. Rate-limit keys protect API endpoints. Online status drives real-time presence. |
| Events Produced | UserRegistered, UserProfileUpdated, UserPreferencesChanged, UserLoggedIn, UserLoggedOut, UserDeactivated | Login/logout events are low-volume but important for audit and real-time presence. |
| Events Consumed | LeadAssigned (updates cached assigned-lead count in profile metadata); NotificationSent (updates unread-count in profile metadata). | Profile aggregate reads events from other aggregates to update lightweight counter caches — never full entity data. |
| Celery Tasks | send_verification_email (sends email confirmation link); send_password_reset_email (sends reset token); purge_expired_sessions (periodic cleanup of expired token rows in DB). | Email sending is async because it depends on an external SMTP service. Session cleanup is maintenance. |
| n8n Workflows | user_onboarding_sequence (watches UserRegistered webhook, enrolls in drip email campaign); user_deactivation_audit (watches UserDeactivated webhook, notifies compliance team via Slack). | Onboarding sequences and compliance notifications are external automations. |
| Public APIs | POST /api/v1/auth/register, POST /api/v1/auth/login, POST /api/v1/auth/logout, GET /api/v1/users/me, PATCH /api/v1/users/me/preferences, POST /api/v1/auth/password-reset | Auth endpoints are public by nature. User profile endpoints require authenticated session. |
| Internal APIs | POST /internal/users/validate (called by API gateway to validate session token and return user_id + roles); GET /internal/users/{id}/permissions (called by other internal services for authorization checks). | Token validation is the gateway's primary auth mechanism. Permission endpoint is used for fine-grained authorization. |
| Dependencies | Tenant aggregate (multi-tenant isolation — user registration checks tenant capacity), Notification aggregate (preferences control notification delivery). | UserProfile reads Tenant for capacity; Notification reads UserProfile for delivery preferences. |

---

## 3.5 KnowledgeDocument Aggregate

Aggregate Root: KnowledgeDocument (document_id)

| Column | Mappings | Rationale |
| --- | --- | --- |
| Aggregate Root | KnowledgeDocument (document_id) | Owns the document content, metadata, version history, and embedding vectors. |
| Application Service | KnowledgeDocumentService | Handles upload, update, delete, search, version creation, and embedding generation. |
| Repository | KnowledgeDocumentRepository | Persists document metadata, content (blob storage reference), and embedding vectors. |
| Database Tables | knowledge_documents, document_versions, document_embeddings, document_tags | knowledge_documents is the root. Embeddings and versions are value objects inside the aggregate. |
| Redis Usage | Key: doc:{id}:content (TTL 1h, caches parsed document text for fast re-read); Key: doc:search:index (in-memory inverted index for lightweight full-text search, rebuilt on document create/update); Key: doc:{id}:lock (write lock during embedding regeneration). | Content cache avoids blob storage fetch on every read. In-memory search index provides fast results without hitting the vector database. Lock prevents concurrent embedding writes. |
| Events Produced | DocumentCreated, DocumentUpdated, DocumentDeleted, DocumentVersionCreated, DocumentEmbeddingGenerated | EmbeddingGenerated signals to search consumers that the document is now vector-searchable. |
| Events Consumed | MeetingEnded (triggers DocumentCreated if meeting summary is saved as a document); LeadQualified (triggers DocumentCreated with enrichment results). | Meeting transcripts and lead enrichment results are written into KnowledgeDocument as side effects of other aggregates' events. |
| Celery Tasks | generate_document_embedding (calls embedding model API, writes vectors to document_embeddings); parse_document_content (extracts text from PDF/DOCX, stores parsed result); ebuild_search_index (periodic full rebuild of Redis search index for consistency). | Embedding generation is the most expensive operation — must be async. Parsing is CPU-bound. Rebuild is a safety net. |
| n8n Workflows | document_external_sync (watches DocumentCreated webhook, syncs to Confluence/Notion); document_backup (periodic, exports documents to external S3 bucket for DR). | External wiki sync and backup are naturally n8n workflows. |
| Public APIs | POST /api/v1/documents, GET /api/v1/documents/{id}, PATCH /api/v1/documents/{id}, DELETE /api/v1/documents/{id}, POST /api/v1/documents/search | Document CRUD and search are exposed to users. |
| Internal APIs | POST /internal/documents/embedding-search (called by RAG pipeline — returns top-K document IDs by vector similarity); GET /internal/documents/{id}/content (called by LLM service to fetch full text for context window). | Embedding search is the backbone of the RAG system. Content fetch is used by the LLM inference service. |
| Dependencies | UserProfile aggregate (document ownership and access control), WorkflowExecution aggregate (documents can trigger workflow executions). | Owner is resolved through UserProfile. Document-triggered workflows are sent as events consumed by WorkflowExecution. |

---

## 3.6 WorkflowExecution Aggregate

Aggregate Root: WorkflowExecution (execution_id)

| Column | Mappings | Rationale |
| --- | --- | --- |
| Aggregate Root | WorkflowExecution (execution_id) | Owns a single run of a workflow/pipeline; tracks state machine (pending/running/blocked/succeeded/failed), inputs, outputs, and step results. |
| Application Service | WorkflowExecutionService | Handles trigger, cancel, retry, and get-status operations. Does NOT define workflow definitions — those are in WorkflowDefinition (a configuration boundary, not a runtime aggregate). |
| Repository | WorkflowExecutionRepository | Persists execution state, step results, and error logs. No other aggregate reads execution data directly. |
| Database Tables | workflow_executions, execution_steps, execution_variables, execution_errors | workflow_executions is the root. Steps and variables are owned by the execution. |
| Redis Usage | Key: wf:exec:{id}:lock (pessimistic lock during step transitions); Key: wf:exec:{id}:state (current state + step index, TTL 24h); Pub/Sub channel wf:exec:{id}:progress for real-time execution UI updates; Key: wf:queue:{worker_group} (list, pending executions by worker type). | Lock prevents duplicate step execution. State cache powers the real-time dashboard. Queue list distributes work across Celery workers. |
| Events Produced | WorkflowTriggered, WorkflowStepCompleted, WorkflowStepFailed, WorkflowCompleted, WorkflowFailed, WorkflowCancelled | Each event carries execution_id and current state for correlation. StepFailed includes error payload for dead-letter analysis. |
| Events Consumed | DocumentCreated (can trigger a workflow that processes the document); LeadCaptured (can trigger lead-scoring workflow); MeetingEnded (can trigger post-meeting workflow). | WorkflowExecution is a generic consumer — it subscribes to events from any aggregate based on tenant-defined workflow rules. |
| Celery Tasks | execute_workflow_step (runs a single step — may call LLM, API, or sub-workflow); timeout_stuck_executions (periodic, marks executions in "running" state for > 1 hour as failed); dead_letter_replay (periodic, retries failed steps up to 3 times). | Step execution is the core Celery workload. Timeout and dead-letter are maintenance tasks. |
| n8n Workflows | workflow_error_alert (watches WorkflowFailed webhook, sends PagerDuty + Slack alert); workflow_analytics_export (periodic, exports execution metrics to Datadog). | Error alerting and metrics export are external integrations. |
| Public APIs | POST /api/v1/workflows/{def_id}/execute, GET /api/v1/workflows/executions/{id}, POST /api/v1/workflows/executions/{id}/cancel, GET /api/v1/workflows/executions (with status filter) | Trigger and status-check endpoints are public to internal apps. |
| Internal APIs | POST /internal/workflows/executions/dead-letter/replay (called by admin panel for manual replay); GET /internal/workflows/executions/stats (called by Dashboard aggregate for execution metrics). | Dead-letter replay and stats are admin-only operations. |
| Dependencies | Tenant aggregate (workflow definitions are tenant-scoped), KnowledgeDocument aggregate (workflow steps read document content for processing). | Workflows operate on documents and belong to tenants, but never access those aggregates' repositories directly — only via events and internal APIs. |

---

## 3.7 Notification Aggregate

Aggregate Root: Notification (notification_id)

| Column | Mappings | Rationale |
| --- | --- | --- |
| Aggregate Root | Notification (notification_id) | Owns the full notification lifecycle: creation, delivery attempt tracking, read status, and dismissal. |
| Application Service | NotificationService | Handles send, mark-read, mark-all-read, dismiss, and get-preferences. |
| Repository | NotificationRepository | Persists notification records and delivery logs. Preferences are stored as a value object on UserProfile but read through this aggregate's service boundary. |
| Database Tables | 
otifications, 
otification_delivery_logs, 
otification_templates | 
otifications is the root. Delivery logs track push/email/in-app delivery status separately. |
| Redis Usage | Key: 
otif:user:{id}:inbox (sorted set, score = created_at, for the last 200 notifications per user); Key: 
otif:user:{id}:unread-count (integer, incremented/decremented atomically); Pub/Sub channel 
otif:user:{id}:new for real-time push to WebSocket connections. | Inbox cache lets the UI load the latest page of notifications without a DB query. Unread count is atomically maintained for the badge counter. Pub/Sub drives instant browser push. |
| Events Produced | NotificationSent, NotificationDelivered, NotificationFailed, NotificationRead, NotificationDismissed | Delivered/failed events are useful for monitoring delivery provider health. Read/dismissed help analytics track user engagement. |
| Events Consumed | MessageAppended (from Conversation — triggers in-app notification for other participants); LeadAssigned (from Lead — triggers notification to assigned sales rep); WorkflowFailed (from WorkflowExecution — triggers alert notification). | Notification aggregate is a passive consumer — it never produces commands to other aggregates. |
| Celery Tasks | send_push_notification (calls FCM/APNs for mobile push); send_email_notification (sends via SES/SendGrid); atch_delivery_retry (periodic, retries failed delivery logs up to 3 times with exponential backoff). | Push and email delivery depend on external providers and must not block the request. Batch retry is a reliability mechanism. |
| n8n Workflows | 
otification_slack_bridge (watches NotificationSent webhook for high-priority notifications, posts to Slack channel); 
otification_sms_fallback (watches NotificationFailed webhook, sends SMS via Twilio as fallback). | Slack bridge and SMS fallback are external channel integrations. |
| Public APIs | POST /api/v1/notifications/send, GET /api/v1/notifications/inbox, PATCH /api/v1/notifications/{id}/read, POST /api/v1/notifications/mark-all-read, DELETE /api/v1/notifications/{id} | Inbox and read/dismiss actions are the core user-facing API. |
| Internal APIs | POST /internal/notifications/send-system (called by any internal service to send system-level notifications bypassing rate limits); GET /internal/notifications/user/{id}/preferences (called by other services to check delivery preferences before emitting events). | System notification endpoint is for alerts from WorkflowExecution, Meeting, etc. Preference check is read-only. |
| Dependencies | UserProfile aggregate (delivery preferences and device tokens), Tenant aggregate (tenant-level notification rate limits). | Reads UserProfile preferences; checks Tenant rate limits before enqueueing deliveries. |

---

## 3.8 PromptVersion Aggregate

Aggregate Root: PromptVersion (prompt_id, version_number)

| Column | Mappings | Rationale |
| --- | --- | --- |
| Aggregate Root | PromptVersion (prompt_id, version_number composite key) | Owns a single prompt template version — content, parameters, model configuration, and evaluation results. |
| Application Service | PromptVersionService | Handles create, update (creates new version), promote-to-production, rollback, diff, and evaluate. |
| Repository | PromptVersionRepository | Persists prompt content, version metadata, and evaluation scores. Every version is immutable after creation. |
| Database Tables | prompt_versions, prompt_evaluations, prompt_parameters | prompt_versions is the root. Evaluations are value objects attached to a specific version. |
| Redis Usage | Key: prompt:active:{prompt_id} (string, stores the production version hash, TTL infinite, manually invalidated on promote); Key: prompt:cache:{prompt_id}:v{version}:{input_hash} (string, cached LLM response, TTL 24h, used for deterministic prompts). | Active version cache avoids a DB read on every LLM call. Response cache saves cost for identical inputs. |
| Events Produced | PromptVersionCreated, PromptVersionPromoted, PromptVersionRolledBack, PromptVersionEvaluated | Promoted/rolled-back events are important for audit trails and A/B test tracking. |
| Events Consumed | WorkflowStepCompleted (if the step used a prompt, the evaluation score is fed back via PromptVersionEvaluated); DocumentUpdated (prompt templates that reference document content may need re-evaluation). | Feedback loop from workflow execution to prompt improvement. |
| Celery Tasks | evaluate_prompt_version (runs a suite of eval test cases against the prompt, computes accuracy/relevance metrics); backtest_prompt_version (re-runs historical LLM calls with the new prompt to measure regression). | Evaluation and backtesting are compute-heavy (LLM calls) and must be async. |
| n8n Workflows | prompt_monitoring_dashboard (watches PromptVersionEvaluated webhook, updates Grafana dashboard with eval metrics); prompt_version_slack_notify (watches PromptVersionPromoted webhook, notifies team in Slack). | Monitoring and team notifications are external integrations. |
| Public APIs | POST /api/v1/prompts, GET /api/v1/prompts/{id}/versions, POST /api/v1/prompts/{id}/versions, PATCH /api/v1/prompts/{id}/promote, GET /api/v1/prompts/{id}/diff?from=v1&to=v2 | Prompt management is a developer-facing API. Diff endpoint enables UI comparison. |
| Internal APIs | GET /internal/prompts/{id}/active (called by WorkflowExecution at runtime to fetch the production prompt content); POST /internal/prompts/{id}/evaluate (called by WorkflowExecution after an LLM step to log evaluation). | Runtime prompt fetch is the highest-volume internal API — must be cached aggressively. Evaluation callback is fire-and-forget. |
| Dependencies | WorkflowExecution aggregate (prompts are used by workflow steps), UserProfile aggregate (prompt authorship and access control). | WorkflowExecution reads prompt content; PromptVersion never reads workflow data. |

---

## 3.9 Tenant Aggregate (Future)

Aggregate Root: Tenant (tenant_id)

| Column | Mappings | Rationale |
| --- | --- | --- |
| Aggregate Root | Tenant (tenant_id) | Owns multi-tenant configuration: plan limits, feature flags, branding, authentication providers, and billing. |
| Application Service | TenantService | Handles provision, update-plan, toggle-feature, update-branding, and deactivate. |
| Repository | TenantRepository | Persists tenant configuration and billing records. All queries are scoped by tenant_id. |
| Database Tables | tenants, tenant_features, tenant_billing_plans, tenant_branding, tenant_auth_providers | tenants is the root. Features, billing, and branding are owned configuration value objects. |
| Redis Usage | Key: tenant:{id}:config (hash, stores feature flags + plan limits, TTL 5 minutes, invalidated on plan/feature change); Key: tenant:{id}:rate-limit (hash of endpoint -> counter, sliding window); Key: tenant:{id}:lock (provisioning lock to prevent double-creation race). | Config cache is read on every API request for feature gating. Rate-limit keys protect shared resources per tenant. Provisioning lock prevents race during signup. |
| Events Produced | TenantProvisioned, TenantPlanChanged, TenantFeatureToggled, TenantDeactivated, TenantBillingUpdated | Plan changed triggers quota recalculation in downstream aggregates. |
| Events Consumed | UserRegistered (checks tenant capacity before allowing registration); WorkflowTriggered (deducts from tenant's monthly execution quota). | Tenant aggregate is a passive validator for other aggregates' operations. |
| Celery Tasks | provision_tenant_resources (creates DB schema, S3 bucket, Redis namespace for new tenant); deactivate_tenant_cleanup (archives tenant data after deactivation grace period); send_billing_invoice (monthly billing cycle, generates and emails invoice). | Provisioning and cleanup are heavyweight operations. Billing is a scheduled cron job. |
| n8n Workflows | tenant_signup_onboarding (watches TenantProvisioned webhook, sends welcome email, creates default admin account); tenant_billing_overdue (watches billing events, triggers dunning email sequence). | External onboarding emails and dunning sequences are n8n automations. |
| Public APIs | POST /api/v1/tenants (provision), GET /api/v1/tenants/{id} (not yet implemented — future), PATCH /api/v1/tenants/{id}/plan (admin), PATCH /api/v1/tenants/{id}/features (admin) | Provision and feature toggle are admin APIs. Tenant GET is deferred to Phase 4. |
| Internal APIs | GET /internal/tenants/{id}/limits (called by every other aggregate's service to check quota before performing an operation); POST /internal/tenants/{id}/validate-feature (called by API gateway to check if a feature is enabled for a tenant). | Quota and feature checks are the primary interaction points — every aggregate calls these before mutating data. |
| Dependencies | UserProfile aggregate (tenant owns users), Notification aggregate (tenant-level rate limits), WorkflowExecution aggregate (tenant-level execution quotas). | Tenant is a dependency of most aggregates but never depends on any of them — it sits at the top of the dependency graph. |

---

## Summary: Aggregate Dependency Graph

The aggregates form a directed acyclic graph. Dependencies always point downward:

Tenant (top) -> UserProfile -> { Conversation, Meeting, Lead, KnowledgeDocument, WorkflowExecution, Notification, PromptVersion }

No aggregate depends on Tenant in a circular manner. Notification and WorkflowExecution are the most intensive event consumers, subscribing to events from 4+ aggregates each.


# 5. Query Handler Mapping

Each query is a read-only operation that bypasses the Domain Layer entirely. Queries are dispatched to dedicated Query Handlers in the Application Layer, which resolve a Read Model by checking Redis cache first (cache-aside pattern) and falling back to the database or vector store on miss. This section maps all 27 queries across the system.

## 5.1 Query Handler Table

| Query | Handler | Read Model | Caching | Database | Redis | Vector Search | Response DTO | API Endpoint |
|---|---|---|---|---|---|---|---|---|
| GetConversation | GetConversationHandler | ConversationReadModel | Redis cache-aside (TTL 5min) | conversations, conversation_messages | conversation:{id}:recent (list, last 50, TTL 1h) | No | ConversationResponse | GET /api/v1/conversations/{id} |
| GetConversationState | GetConversationStateHandler | ConversationStateReadModel | Redis (TTL 1min) | conversations | conversation:{id}:state (hash) | No | ConversationStateResponse | GET /api/v1/conversations/{id}/state |
| GetActiveConversations | GetActiveConversationsHandler | ActiveConversationsReadModel | Redis sorted set (TTL 5min) | conversations WHERE active=true | user:{id}:active-conversations (sorted set) | No | ActiveConversationsResponse | GET /api/v1/conversations/active |
| GetMeeting | GetMeetingHandler | MeetingReadModel | Redis cache-aside (TTL 5min) | meetings | meeting:{id}:state (hash) | No | MeetingResponse | GET /api/v1/meetings/{id} |
| GetUserMeetings | GetUserMeetingsHandler | UserMeetingsReadModel | Redis sorted set (TTL 2min) | meetings JOIN meeting_participants | user:{id}:meetings (sorted set) | No | UserMeetingsResponse | GET /api/v1/meetings |
| GetMeetingAvailability | GetMeetingAvailabilityHandler | MeetingAvailabilityReadModel | Redis time-slot cache (TTL 30s) | meetings (existing bookings) | meeting:availability:{date}:{user} (bitmap) + slot locks | No | MeetingAvailabilityResponse | GET /api/v1/meetings/availability |
| GetUserMeetingsByDate | GetUserMeetingsByDateHandler | UserMeetingsByDateReadModel | Redis sorted set (TTL 1min) | meetings JOIN meeting_participants WITH date filter | user:{id}:meetings:{date} (sorted set) | No | UserMeetingsByDateResponse | GET /api/v1/meetings?date={date} |
| GetLead | GetLeadHandler | LeadReadModel | Redis cache-aside (TTL 5min) | leads | lead:{id} (hash) | No | LeadResponse | GET /api/v1/leads/{id} |
| SearchLeads | SearchLeadsHandler | LeadSearchReadModel | Redis (TTL 2min) | leads (full-text search) | lead:search:{query_hash} (sorted set) | Yes (optional semantic) | SearchLeadsResponse | GET /api/v1/leads?q={query} |
| GetQualifiedLeads | GetQualifiedLeadsHandler | QualifiedLeadsReadModel | Redis sorted set (TTL 2min) | leads WHERE qualified=true | lead:score-queue (sorted set) | No | QualifiedLeadsResponse | GET /api/v1/leads/qualified |
| GetUserProfile | GetUserProfileHandler | UserProfileReadModel | Redis cache-aside (TTL 10min) | user_profiles | user:{id}:profile (hash) | No | UserProfileResponse | GET /api/v1/users/me |
| GetUserPreferences | GetUserPreferencesHandler | UserPreferencesReadModel | Redis (TTL 10min) | user_preferences | user:{id}:preferences (hash) | No | UserPreferencesResponse | GET /api/v1/users/me/preferences |
| GetConversationSummary | GetConversationSummaryHandler | ConversationSummaryReadModel | Redis (TTL 1h) | conversation_messages (aggregated) | conversation:{id}:summary (string) | No | ConversationSummaryResponse | GET /api/v1/conversations/{id}/summary |
| SearchSemanticMemory | SearchSemanticMemoryHandler | SemanticMemoryReadModel | Redis (TTL 5min) | conversation_messages | memory:{user}:semantic:{query_hash} (string) | Yes (embedding similarity) | SemanticMemoryResponse | POST /api/v1/memory/semantic-search |
| SearchKnowledge | SearchKnowledgeHandler | KnowledgeSearchReadModel | Redis hybrid (TTL 5min) | knowledge_documents (metadata filter) | doc:search:cache:{query_hash} (string) | Yes (primary retrieval) | SearchKnowledgeResponse | POST /api/v1/documents/search |
| GetDocument | GetDocumentHandler | DocumentReadModel | Redis cache-aside (TTL 1h) | knowledge_documents | doc:{id}:content (string) | No | DocumentResponse | GET /api/v1/documents/{id} |
| GetWorkflowStatus | GetWorkflowStatusHandler | WorkflowStatusReadModel | Redis (TTL 30s) | workflow_executions | wf:exec:{id}:state (hash) | No | WorkflowStatusResponse | GET /api/v1/workflows/executions/{id} |
| GetNotificationStatus | GetNotificationStatusHandler | NotificationStatusReadModel | Redis (TTL 1min) | notifications | notif:{id}:status (hash) | No | NotificationStatusResponse | GET /api/v1/notifications/{id} |
| GetPendingNotifications | GetPendingNotificationsHandler | PendingNotificationsReadModel | Redis sorted set (TTL 1min) | notifications WHERE status=pending | notif:user:{id}:inbox (sorted set) | No | PendingNotificationsResponse | GET /api/v1/notifications/inbox?status=pending |
| GetPromptVersion | GetPromptVersionHandler | PromptVersionReadModel | Redis (TTL 1h) | prompt_versions | prompt:cache:{prompt_id}:v{version} (string) | No | PromptVersionResponse | GET /api/v1/prompts/{id}/versions/{version} |
| GetActivePrompt | GetActivePromptHandler | ActivePromptReadModel | Redis (TTL 1h, invalidate on promote) | prompt_versions WHERE active=true | prompt:active:{prompt_id} (string) | No | ActivePromptResponse | GET /api/v1/prompts/{id}/active |
| ListPromptVersions | ListPromptVersionsHandler | PromptVersionListReadModel | Redis (TTL 5min, invalidate on new version) | prompt_versions | prompt:versions:{prompt_id} (list) | No | PromptVersionListResponse | GET /api/v1/prompts/{id}/versions |
| GetUserIdentity | GetUserIdentityHandler | UserIdentityReadModel | Redis (TTL 10min) | user_profiles | user:{id}:identity (hash) | No | UserIdentityResponse | GET /api/v1/users/me/identity |
| CheckPermission | CheckPermissionHandler | PermissionReadModel | Redis (TTL 2min) | user_profiles JOIN roles | user:{id}:permissions:{resource} (set) | No | CheckPermissionResponse | POST /api/v1/auth/check-permission |
| GetSystemHealth | GetSystemHealthHandler | SystemHealthReadModel | No caching (real-time) | Connection pool check | PING + health keys | No | SystemHealthResponse | GET /api/v1/health |
| GetMetrics | GetMetricsHandler | MetricsReadModel | Redis (TTL 30s) | Aggregated metrics query | metrics:{scope}:{period} (hash) | No | MetricsResponse | GET /api/v1/metrics |
| GetConversationAnalytics | GetConversationAnalyticsHandler | ConversationAnalyticsReadModel | Redis (TTL 5min) | Aggregate queries on conversations + messages | analytics:conversation:{scope} (hash) | No | ConversationAnalyticsResponse | GET /api/v1/analytics/conversations |

## 5.2 Detailed Query Explanations

### 5.2.1 GetConversation — Multi-Layer Cache + State Check

The GetConversation query is the highest-volume read path in the system, serving every conversation-load operation from the web UI, mobile app, and real-time reconnections. Its handler executes three phases in sequence:

    Phase 1 — Distributed Lock Acquisition
    Before reading, the handler attempts a non-blocking Redis distributed lock on
    conversation:{id}:lock (NX + TTL 200ms). If the lock is acquired, this
    instance is responsible for refreshing the cache. If not, the handler proceeds
    to read from the existing cache or DB — stale data is acceptable for the brief
    lock window. This prevents the thundering-herd problem when N clients
    reconnect simultaneously (e.g., after a WebSocket disconnect).

    Phase 2 — Cache-Aside Read
    The handler checks Redis key conversation:{id}:recent (a list capped at 50
    messages, TTL 1 hour). On cache hit, it deserializes the list into
    ConversationReadModel and returns immediately, skipping the database
    entirely. This path completes in under 5ms.

    On cache miss, the handler loads the full conversation from the
    conversations and conversation_messages tables via ConversationRepository,
    limiting to the last 100 messages (pagination offset is passed as a query
    parameter). The loaded messages are written to conversation:{id}:recent
    (LPUSH + LTRIM to maintain the 50-message cap) and the TTL is refreshed.

    Phase 3 — Conversation State Validation
    Once the conversation data is resolved, the handler performs a state
    validation check:

        Check conversation:{id}:state in Redis for the current status
        (active / archived / deleted). If Redis is empty, fall back to the
        conversations table state column.
        If the conversation is archived or deleted, the handler appends a
        metadata flag (is_archived, archived_at) to the response DTO rather
        than returning a 404. The client displays the conversation in a
        read-only "archive" view.

    Response Assembly
    The final ConversationResponse DTO is assembled from the cached messages,
    participant list (from conversation_participants sub-cache), and state
    metadata. No domain logic is executed — this is a pure read projection.

### 5.2.2 SearchKnowledge — Vector Search + Re-ranking + Cache Fusion

The SearchKnowledge query powers the RAG pipeline and the knowledge-base search interface. It combines dense vector retrieval with lightweight caching and cross-encoder re-ranking:

    Phase 1 — Query Normalization and Cache Check
    The incoming query string is normalized (lowercased, stop-word removal,
    whitespace trimming) and hashed with SHA-256 to produce a cache key:

        doc:search:cache:{query_hash}

    The handler checks Redis for this key. On cache hit, the stored result
    (serialized list of top-10 document IDs + relevance scores) is returned
    immediately. The TTL is 5 minutes for identical queries, but a secondary
    TTL of 30 seconds is applied if the original search used filters —
    filtered results are invalidated more aggressively.

    Phase 2 — Vector Search (Primary Retrieval)
    On cache miss, the handler calls the RAG service embedding endpoint to
    generate a query vector (768-dimensional embedding using the same encoder
    model used for document ingestion). The vector is sent to the vector store
    (Pinecone / Qdrant via the infrastructure/vector_store adapter) with these
    parameters:

        top_k: 50 (candidate pool)
        ef_search: 256 (HNSW search breadth)
        namespace: tenant_id (multi-tenant isolation)
        filter: document_tags, date_range, document_type (optional)

    The vector store returns the top-50 document IDs with cosine similarity
    scores. This set is the candidate pool for re-ranking.

    Phase 3 — Cross-Encoder Re-ranking
    The 50 candidate documents are passed to a cross-encoder model (e.g.
    BAAI/bge-reranker-v2-m3) running on a GPU inference endpoint. The
    cross-encoder scores each (query, document) pair with a deeper relevance
    computation than cosine similarity:

        pairs = [(query, doc1), (query, doc2), ..., (query, doc50)]
        scores = cross_encoder(pairs)  # returns 50 float scores

    The documents are re-sorted by cross-encoder score and the top-5 results
    are selected for the final response. This two-stage retrieval (bi-encoder
    recall + cross-encoder precision) consistently outperforms single-stage
    vector search in retrieval metrics.

    Phase 4 — Metadata Enrichment and Caching
    For each of the top-5 document IDs, the handler fetches metadata from the
    knowledge_documents table (title, snippet, tags, updated_at) and assembles
    the SearchKnowledgeResponse DTO. The full result (query hash -> top-5 IDs
    + scores) is written to Redis with the 5-minute TTL.

    If the re-ranker service is unavailable (degraded mode), the handler falls
    back to the raw vector similarity scores — this reduces quality but
    maintains availability.

### 5.2.3 GetMeetingAvailability — Calendar Check + Redis Slot Locks + Cached Availability

The GetMeetingAvailability query is the most latency-sensitive read in the system — users expect sub-200ms responses when viewing the meeting scheduler calendar. It combines three data sources to compute real-time slot availability:

    Phase 1 — Cached Availability Window
    The handler computes a cache key from the user ID and the requested date:

        meeting:availability:{user_id}:{YYYY-MM-DD}

    This Redis key stores a bitmap of 96 slots (15-minute intervals from
    00:00 to 23:45). A set bit means "available"; a cleared bit means "booked
    or locked". On cache hit, the bitmap is returned directly — the handler
    skips phases 2 and 3.

    On cache miss (or after TTL expiry of 30 seconds), the handler proceeds to
    Phase 2 to rebuild the bitmap. The 30-second TTL is intentionally short
    because availability changes in real-time as users book slots.

    Phase 2 — Calendar Booking Check
    The handler queries the meetings table for all meetings on the requested
    date where the requesting user is a participant:

        SELECT start_time, end_time, status
        FROM meetings m
        JOIN meeting_participants mp ON m.meeting_id = mp.meeting_id
        WHERE mp.user_id = :user_id
          AND m.start_time::date = :requested_date
          AND m.status IN ('scheduled', 'active');

    For each booked meeting, the handler clears the corresponding bits in the
    bitmap (start_time to end_time, rounded to 15-minute intervals). This
    establishes the "definitely booked" slots from persistent storage.

    Phase 3 — Redis Slot Lock Check (Soft Booking)
    Slots that are not booked in the database may still be temporarily locked
    by other users who are in the process of booking. The handler checks Redis
    sorted set keys of the form:

        meeting:slot-locks:{YYYY-MM-DD}

    Where each member is a slot identifier (e.g., "09:00-09:15") and the score
    is the lock expiry Unix timestamp (TTL = 2 minutes from acquisition). If a
    slot has an active lock, the corresponding bitmap bits are cleared (marked
    unavailable).

    This prevents double-booking during the window between "user clicks book"
    and "transaction commits" — without requiring database-level locking or
    serializable isolation levels.

    Phase 4 — Bitmap Rebuild and Response
    The final bitmap (96 bits, stored as an 12-byte binary string) is written
    to meeting:availability:{user_id}:{YYYY-MM-DD} with TTL 30 seconds. The
    handler assembles the MeetingAvailabilityResponse DTO:

    {
        "date": "2026-07-15",
        "slots": [
            {"time": "09:00", "available": true},
            {"time": "09:15", "available": true},
            {"time": "09:30", "available": false},
            ...
        ],
        "timezone": "America/New_York",
        "cached_at": "2026-07-14T22:00:00Z"
    }

    The response is returned with Cache-Control: private, max-age=30 to allow
    the API gateway to serve stale-from-cache responses during traffic spikes.

# 4. Command Handler Mapping

Each command flows through a defined pipeline. The tables below map every command to its handler,
application service, validation rules, repository, produced events, Celery task, saga coordinator,
API endpoint, response type, and failure strategy. Commands are grouped by domain aggregate.

---

## 4.1 Conversation Commands

| Command | Command Handler | Application Service | Validation | Repository | Events | Celery Task | Saga | API Endpoint | Response | Failure Strategy |
|---|---|---|---|---|---|---|---|---|---|---|
| HandleMessage | HandleMessageHandler | MessageProcessingService | MessagePayloadValidator, ConversationActiveValidator, ParticipantValidator, RateLimitValidator | ConversationRepository, MemoryRepository, UserProfileRepository | MessageReceived, IntentClassified, ToolExecutionRequested, MemoryUpdated, ResponseGenerated | process_message_async | MessageProcessingSaga | POST /api/v1/conversations/{id}/messages | MessageResponse (streamed SSE or complete JSON) | Retry 3x (exponential backoff) -> Dead letter queue -> Human handoff request |
| StartConversation | StartConversationHandler | ConversationService | CreateConversationValidator, ParticipantLimitValidator, TenantQuotaValidator | ConversationRepository, UserProfileRepository | ConversationCreated, ParticipantAdded | start_conversation_notify | None (fire-and-forget notification) | POST /api/v1/conversations | ConversationResponse (id, participants, created_at) | Return 409 on duplicate -> Return 422 on validation failure |
| ResumeConversation | ResumeConversationHandler | ConversationService | ConversationExistsValidator, ConversationArchivedValidator, ParticipantValidator | ConversationRepository, MemoryRepository | ConversationResumed | restore_conversation_context | None | POST /api/v1/conversations/{id}/resume | ConversationResumeResponse (recent messages, memory context, state) | Return 404 if archived -> Return 410 if deleted |
| ArchiveConversation | ArchiveConversationHandler | ConversationService | ConversationExistsValidator, AlreadyArchivedValidator, PermissionValidator | ConversationRepository | ConversationArchived | expire_conversation_cache | None | DELETE /api/v1/conversations/{id} | ArchiveResponse (archived_at, message_count) | Return 404 if not found -> Soft delete only |

---

## 4.2 Meeting Commands

| Command | Command Handler | Application Service | Validation | Repository | Events | Celery Task | Saga | API Endpoint | Response | Failure Strategy |
|---|---|---|---|---|---|---|---|---|---|---|
| ScheduleMeeting | ScheduleMeetingHandler | MeetingService | MeetingRequestValidator, AvailabilityValidator, ParticipantConflictValidator, TimeSlotValidator | MeetingRepository, UserProfileRepository | MeetingScheduled | send_meeting_notifications | MeetingScheduleSaga | POST /api/v1/meetings | MeetingResponse (id, time, participants, status) | Compensating transaction on availability failure -> Notify organizer on partial failure |
| CancelMeeting | CancelMeetingHandler | MeetingService | MeetingExistsValidator, CancelPolicyValidator (notice period), PermissionValidator | MeetingRepository | MeetingCancelled | notify_cancellation | None | POST /api/v1/meetings/{id}/cancel | CancelResponse (cancelled_at, refund_status) | Return 409 if already ended -> Log reason for audit |
| RescheduleMeeting | RescheduleMeetingHandler | MeetingService | MeetingExistsValidator, NewTimeSlotValidator, ParticipantConflictValidator, ReschedulePolicyValidator | MeetingRepository | MeetingRescheduled | notify_reschedule | RescheduleSaga | PATCH /api/v1/meetings/{id} | MeetingResponse (updated time, status) | Compensate on participant conflict -> Retry with alternative slots |
| ConfirmMeeting | ConfirmMeetingHandler | MeetingService | MeetingExistsValidator, ConfirmationDeadlineValidator, ParticipantResponseValidator | MeetingRepository | MeetingConfirmed, ParticipantConfirmed | confirm_meeting_reminder | None | POST /api/v1/meetings/{id}/confirm | ConfirmationResponse (confirmed_participants, status) | Return 410 if expired -> Escalate to organizer on deadline miss |

---

## 4.3 Lead Commands

| Command | Command Handler | Application Service | Validation | Repository | Events | Celery Task | Saga | API Endpoint | Response | Failure Strategy |
|---|---|---|---|---|---|---|---|---|---|---|
| CreateLead | CreateLeadHandler | LeadService | EmailUniquenessValidator, RequiredFieldValidator, DuplicateDetectionValidator (Redis dedup), TenantQuotaValidator | LeadRepository, UserProfileRepository | LeadCaptured | enrich_lead_with_data, score_lead | LeadCreationSaga | POST /api/v1/leads | LeadResponse (id, score, enrichment_status) | Dedup silently on duplicate email (return existing) -> Dead letter on enrichment failure |
| QualifyLead | QualifyLeadHandler | LeadService | LeadExistsValidator, AlreadyQualifiedValidator, ScoreThresholdValidator, AssignmentValidator | LeadRepository | LeadQualified, LeadAssigned | score_lead_batch, notify_lead_assignment | LeadQualificationSaga | PATCH /api/v1/leads/{id}/qualify | QualificationResponse (score, tier, assigned_to) | Return 409 if already qualified -> Fallback to manual qualification on scoring failure |

---

## 4.4 Memory Commands

| Command | Command Handler | Application Service | Validation | Repository | Events | Celery Task | Saga | API Endpoint | Response | Failure Strategy |
|---|---|---|---|---|---|---|---|---|---|---|
| UpdateMemory | UpdateMemoryHandler | MemoryService | MemoryFieldValidator, ConfirmationPolicyValidator, EmbeddingSizeValidator | MemoryRepository, ConversationRepository | MemoryUpdateRequested, MemoryFieldConfirmed, MemoryUpdated, MemoryEmbeddingUpdated | update_memory_embedding, reindex_memory | MemoryUpdateSaga | PATCH /api/v1/memory | MemoryUpdateResponse (field, value, confirmation_required, embedding_status) | Rollback embedding on failure -> Flag for manual review on field conflict -> Retry embedding on timeout |
| ConfirmMemoryField | ConfirmMemoryFieldHandler | MemoryService | ConfirmationTokenValidator, FieldExistsValidator, ExpiryValidator | MemoryRepository, ConversationRepository | MemoryFieldConfirmed, MemoryUpdated | update_memory_embedding | None | POST /api/v1/memory/confirm | ConfirmationResponse (confirmed, updated_at) | Return 410 on expired token -> Return 404 on invalid field reference |

---

## 4.5 Workflow Commands

| Command | Command Handler | Application Service | Validation | Repository | Events | Celery Task | Saga | API Endpoint | Response | Failure Strategy |
|---|---|---|---|---|---|---|---|---|---|---|
| ExecuteWorkflow | ExecuteWorkflowHandler | WorkflowExecutionService | WorkflowDefExistsValidator, InputSchemaValidator, TenantQuotaValidator, RateLimitValidator | WorkflowExecutionRepository, WorkflowDefinitionRepository | WorkflowTriggered, WorkflowStepCompleted, WorkflowCompleted | execute_workflow_step, timeout_stuck_executions | WorkflowExecutionSaga | POST /api/v1/workflows/{def_id}/execute | ExecutionResponse (execution_id, status, initial_step) | Retry step 3x -> Dead letter step -> Fail execution -> Notify admin |
| CompensateWorkflow | CompensateWorkflowHandler | WorkflowExecutionService | ExecutionExistsValidator, CompensatableValidator, ExecutionStateValidator | WorkflowExecutionRepository | WorkflowCompensationStarted, WorkflowStepCompensated, WorkflowCompensationCompleted | compensate_workflow_step | CompensationSaga | POST /api/v1/workflows/executions/{id}/compensate | CompensationResponse (execution_id, compensation_status, steps_compensated) | Fail whole compensation on step failure -> Manual remediation required |

---

## 4.6 Notification Commands

| Command | Command Handler | Application Service | Validation | Repository | Events | Celery Task | Saga | API Endpoint | Response | Failure Strategy |
|---|---|---|---|---|---|---|---|---|---|---|
| GenerateSummary | GenerateSummaryHandler | SummaryService | ConversationExistsValidator, SummaryPolicyValidator, TokenLimitValidator | ConversationRepository, MemoryRepository, KnowledgeDocumentRepository | SummaryGenerated, SummarySaved | generate_conversation_summary | None | POST /api/v1/conversations/{id}/summary | SummaryResponse (summary_text, key_points, token_count) | Fallback to extractive summary on LLM failure -> Return partial summary on timeout |
| TriggerNotification | TriggerNotificationHandler | NotificationService | TemplateExistsValidator, RecipientValidator, RateLimitValidator, PreferenceValidator | NotificationRepository, UserProfileRepository, TenantRepository | NotificationSent, NotificationDelivered | send_push_notification, send_email_notification | None | POST /api/v1/notifications/send | NotificationResponse (id, channel, status) | Failover channel on delivery failure -> Dead letter after 3 retries -> Log delivery failure |
| SendTestNotification | SendTestNotificationHandler | NotificationService | RecipientValidator, TemplateExistsValidator, TestModeValidator | NotificationRepository | NotificationTestSent | none (synchronous for test) | None | POST /api/v1/notifications/test | TestNotificationResponse (delivered, preview_url) | Return detailed error on failure (for debugging) |

---

## 4.7 System Commands

| Command | Command Handler | Application Service | Validation | Repository | Events | Celery Task | Saga | API Endpoint | Response | Failure Strategy |
|---|---|---|---|---|---|---|---|---|---|---|
| ClassifyIntent | ClassifyIntentHandler | IntentClassificationService | MessageRequiredValidator, TenantModelValidator, InputLengthValidator | PromptVersionRepository, ConversationRepository | IntentClassified | none (synchronous for classification) | None | POST /api/v1/intent/classify | IntentResponse (intent, confidence, entities, alternatives) | Fallback to rule-based classifier on model failure -> Return low-confidence with alternatives |
| ExecuteTool | ExecuteToolHandler | ToolExecutionService | ToolExistsValidator, ArgumentSchemaValidator, PermissionValidator, RateLimitValidator | ToolRegistryRepository | ToolExecutionStarted, ToolExecutionSucceeded, ToolExecutionFailed | execute_tool_async | ToolExecutionSaga | POST /api/v1/tools/execute | ToolResponse (result, execution_time_ms, status) | Retry idempotent tools 3x -> Return error for non-idempotent -> Escalate on auth failure |
| RequestHumanHandoff | RequestHumanHandoffHandler | HumanHandoffService | HandoffPolicyValidator, AgentAvailabilityValidator, ConversationExistsValidator, PriorityValidator | ConversationRepository, UserProfileRepository | HumanHandoffRequested, AgentAssigned | assign_human_agent | HandoffSaga | POST /api/v1/conversations/{id}/handoff | HandoffResponse (ticket_id, estimated_wait_time, agent_id if available) | Fallback to voicemail on no available agent -> Queue with priority -> Notify on agent assignment |

---

## 4.8 Detailed Command Explanations

---

### HandleMessage

HandleMessage is the most complex command in the system. It spans identity resolution, intent
classification, conversation state management, memory read/write, tool execution, and LLM
response generation. The diagram below shows the full execution path:

    ┌─────────────────────────────────────────────────────────────────────┐
    │  POST /api/v1/conversations/{id}/messages                          │
    │  HandleMessageCommand { conversation_id, content, metadata }       │
    └─────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  1. Identity Resolution                                            │
    │  ResolveUserIdService extracts tenant_id, user_id, roles from      │
    │  the session token attached by middleware. For anonymous users,     │
    │  a temporary identity is created in Redis with TTL. The resolved    │
    │  identity is attached to the command metadata for downstream use.   │
    └─────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  2. Validation Pipeline                                            │
    │  a) MessagePayloadValidator — ensures content is not empty,         │
    │     within max length (4096 chars), and passes content policy.      │
    │  b) ConversationActiveValidator — checks the conversation is not    │
    │     archived or deleted.                                            │
    │  c) ParticipantValidator — verifies the sender is a participant.    │
    │  d) RateLimitValidator — enforces per-user and per-tenant message   │
    │     rate limits (sliding window in Redis).                          │
    └─────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  3. Persist Message & Publish MessageReceived                      │
    │  ConversationRepository.append_message(conversation_id, message)    │
    │  appends the new message to the Conversation aggregate. After       │
    │  persistence, MessageReceived domain event is emitted to trigger    │
    │  downstream processing.                                            │
    └─────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  4. Celery Async — process_message_async                           │
    │  The saga continues asynchronously in the Celery worker to avoid    │
    │  blocking the HTTP response. The worker executes:                   │
    └─────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │  4a. Intent Classification                                     │
        │  IntentClassificationService.classify(message, context) calls   │
        │  the LLM with a few-shot prompt from PromptVersionRepository.   │
        │  Returns intent (create_lead, schedule_meeting, ask_question,   │
        │  execute_tool, etc.) and extracted entities. Low-confidence     │
        │  results fall back to a rule-based classifier.                  │
        │  Emits: IntentClassified event.                                │
        └─────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │  4b. Memory Read & Update                                      │
        │  MemoryRepository.read(conversation_id) loads relevant memory   │
        │  fields for the conversation. MemoryService merges new facts    │
        │  extracted from the message (via LLM extraction prompt) into    │
        │  working memory. If a field requires user confirmation, the     │
        │  update is staged as pending and MemoryUpdateRequested event    │
        │  is emitted. Immediate updates emit MemoryUpdated.              │
        └─────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │  4c. Tool Execution (if applicable)                            │
        │  If the classified intent requires a tool (e.g. CreateLead,     │
        │  ScheduleMeeting), ToolExecutionService.execute(tool_name,      │
        │  args) validates arguments against the tool schema, runs the    │
        │  tool, and captures the result. The tool output is injected     │
        │  into the LLM context for response generation.                  │
        │  Emits: ToolExecutionRequested, ToolExecutionSucceeded/Failed.  │
        └─────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │  4d. LLM Response Generation                                   │
        │  ResponseGenerationService.generate(context) assembles the      │
        │  full context: recent messages, memory snapshot, tool results,  │
        │  and system prompt (from PromptVersionRepository). Calls the    │
        │  LLM with streaming (SSE) or non-streaming mode. The generated  │
        │  response is appended as an assistant message to the            │
        │  Conversation aggregate via ConversationRepository.             │
        │  Emits: ResponseGenerated.                                      │
        └─────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │  4e. Post-Processing                                           │
        │  - update_memory_embedding Celery task updates vector index.    │
        │  - If tool execution created a side-effect (e.g. lead created), │
        │    the response includes the reference ID.                      │
        │  - Conversation cache in Redis is refreshed.                    │
        └─────────────────────────────────────────────────────────────────┘

Failure strategy for HandleMessage:

    The overall saga uses a compensating transaction model. If any step
    fails after the message is persisted (step 3), the following occurs:
    - Step 4a (classification) failure: Fallback to "unknown" intent;
      the LLM is prompted to classify without context. No compensation.
    - Step 4b (memory) failure: Memory update is skipped; the message
      is still responded to. A Dead letter record is created for manual
      memory reconciliation.
    - Step 4c (tool) failure: The error is injected into the LLM context
      so the assistant can communicate the failure to the user.
      Compensating tool calls (e.g. cancel created lead) are queued as
      a follow-up.
    - Step 4d (LLM) failure: Retry 2x with reduced context window. If
      still failing, a fallback response ("I'm having trouble processing
      your request") is appended and a human handoff is requested.

---

### ScheduleMeeting

ScheduleMeeting coordinates the Meeting aggregate, availability verification,
participant conflict detection, calendar integration, and notification
delivery. It also triggers an n8n workflow for external calendar sync.

    ┌─────────────────────────────────────────────────────────────────────┐
    │  POST /api/v1/meetings                                             │
    │  ScheduleMeetingCommand { title, start_time, end_time,              │
    │    participants[], description, conference_provider }               │
    └─────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  1. Validation                                                     │
    │  a) MeetingRequestValidator — required fields, time range           │
    │     (start < end, min 15min, max 4h), valid conference provider.   │
    │  b) AvailabilityValidator — queries UserProfileRepository for each  │
    │     participant's calendar to verify no existing meetings overlap   │
    │     (Redis cached busy slots).                                     │
    │  c) ParticipantConflictValidator — checks a participant is not      │
    │     already double-booked.                                         │
    │  d) TimeSlotValidator — respects business hours and tenant-         │
    │     configured meeting windows.                                    │
    └─────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  2. Create Meeting Aggregate                                        │
    │  MeetingService.schedule(command) creates a new Meeting aggregate   │
    │  root with status = scheduled. Participants are added as value      │
    │  objects. The conference link is provisioned (Google Meet / Zoom    │
    │  API call via infrastructure adapter).                             │
    │  Repository: MeetingRepository.save(meeting).                       │
    └─────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  3. Publish Domain Event: MeetingScheduled                          │
    │  The event carries meeting_id, time, participant list, and          │
    │  conference URL. Downstream consumers react:                        │
    └─────────────────────────┬───────────────────────────────────────────┘
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
    ┌────────────────────────────┐  ┌────────────────────────────────────┐
    │  Celery:                   │  │  n8n Webhook:                     │
    │  send_meeting_notifications │  │  meeting_calendar_sync            │
    │  - Sends calendar invites   │  │  - Creates Google Calendar event  │
    │    via email (iCal attach). │  │  - Creates Outlook event           │
    │  - Sends in-app push        │  │  - Posts to Slack channel          │
    │    notification.            │  │  (configured per tenant)           │
    │  - Respects delivery        │  └────────────────────────────────────┘
    │    preferences from         │
    │    UserProfile.             │
    └────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │  4. Saga: MeetingScheduleSaga                                       │
    │  The saga coordinator tracks the following steps:                   │
    │  a) Availability reserved (Redis temporary lock on time slots).    │
    │  b) Meeting aggregate persisted.                                   │
    │  c) Conference link provisioned.                                   │
    │  d) Notifications sent (fire-and-forget, does not block).          │
    │  e) n8n webhook delivered (fire-and-forget).                       │
    │                                                                    │
    │  If step (b) fails: Release availability locks, return error.      │
    │  If step (c) fails: Cancel meeting, notify organizer via fallback  │
    │    channel (email).                                                │
    │  Steps (d) and (e) are best-effort; failure does not roll back     │
    │  the meeting. Dead letter records are created for retry.           │
    └─────────────────────────────────────────────────────────────────────┘

Failure strategy for ScheduleMeeting:

    The saga has a strict ordering for compensating actions. Reservations
    in Redis (step a) have a TTL equal to the meeting start time and are
    released immediately if the meeting creation fails. Conference
    provisioning failures (step c) trigger an immediate cancellation of
    the meeting (compensating action) and an urgent notification to the
    organizer. Notification failures (step d) are retried by the Celery
    worker with exponential backoff up to 3 attempts; if all fail, the
    meeting remains scheduled but a Dead letter is logged for ops review.
    The n8n webhook (step e) is non-blocking — if the webhook endpoint is
    unreachable, the webhook is retried by the n8n source with its own
    retry policy.

---

### UpdateMemory

UpdateMemory operates on the Memory aggregate, which is a child of the
Conversation aggregate. It handles field-level memory updates with a
confirmation policy (some fields require explicit user confirmation before
they are committed), embedding vector regeneration, and reindexing.

    ┌─────────────────────────────────────────────────────────────────────┐
    │  PATCH /api/v1/memory                                              │
    │  UpdateMemoryCommand { conversation_id, field, value, context }    │
    └─────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  1. Validation                                                     │
    │  a) MemoryFieldValidator — field name must exist in the memory      │
    │     schema registry. Value type must match the schema type          │
    │     (string, number, date, entity_ref, list).                      │
    │  b) ConfirmationPolicyValidator — checks the field's confirmation   │
    │     policy. Fields marked "auto" are committed immediately. Fields │
    │     marked "confirm" require explicit user confirmation via         │
    │     ConfirmMemoryField command.                                    │
    │  c) EmbeddingSizeValidator — if the field contributes to vector     │
    │     search, the value must not exceed the max embedding input       │
    │     length (8192 tokens).                                          │
    │                                                                    │
    │  Context parameter is optional text describing why the memory is    │
    │  being updated. Used for audit trails and for the LLM to explain   │
    │  changes to the user.                                              │
    └─────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  2. Confirmation Policy Branch                                      │
    │  MemoryService.update(field, value, context) evaluates the field's  │
    │  confirmation_policy:                                              │
    │                                                                    │
    │  Case "auto":                                                       │
    │    - Write value to Memory aggregate immediately.                   │
    │    - Emit MemoryUpdated event.                                      │
    │    - Continue to step 3.                                            │
    │                                                                    │
    │  Case "confirm":                                                    │
    │    - Stage the update as pending in the Memory aggregate.           │
    │    - Generate a confirmation token (UUID, stored in Redis with      │
    │      TTL 15 minutes).                                               │
    │    - Emit MemoryUpdateRequested event (includes token).             │
    │    - Response to client includes confirmation_required: true        │
    │      and the token.                                                 │
    │    - The update is NOT written to the long-term memory until        │
    │      ConfirmMemoryField is called with the token.                   │
    │    - Stop here; no embedding update until confirmed.                │
    └─────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  3. Celery Async — update_memory_embedding                          │
    │  For "auto" confirmed fields, the Celery worker:                   │
    │  a) Reads the updated Memory aggregate for the conversation.        │
    │  b) Constructs the memory string by concatenating all memory        │
    │     fields in the configured template order.                        │
    │  c) Calls the embedding model API to generate a new vector.         │
    │  d) Stores the vector in the document_embeddings table via          │
    │     MemoryRepository.                                               │
    │  e) Emits MemoryEmbeddingUpdated event.                             │
    │                                                                    │
    │  After embedding is stored, the reindex_memory Celery task:        │
    │  f) Updates the Redis vector search index with the new embedding.   │
    │  g) Invalidates the conversation context cache in Redis.            │
    └─────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  4. Saga: MemoryUpdateSaga                                          │
    │  The saga tracks:                                                   │
    │  a) Memory field written (or staged for confirmation).             │
    │  b) Embedding generation initiated.                                │
    │  c) Embedding stored in database.                                  │
    │  d) Vector index updated.                                          │
    │                                                                    │
    │  If step (b) fails: Retry 2x. If persistent failure, the memory    │
    │    update is committed but flagged for offline reindexing.         │
    │  If step (c) fails: The embedding is lost but the memory value is  │
    │    preserved. A Dead letter is created for ops to reindex.         │
    │  If step (d) fails: The conversation still works with pre-update   │
    │    embeddings. The task is retried on the next conversation access. │
    └─────────────────────────────────────────────────────────────────────┘

Failure strategy for UpdateMemory:

    The guiding principle is that the memory value is always preserved even
    if the embedding fails. Memory field writes (steps 1-2) execute within
    the HTTP request transaction; only success returns a 200. If the write
    succeeds, the response is sent before the embedding pipeline runs. If
    the embedding pipeline fails entirely:
    - The Memory aggregate retains the updated field value.
    - The MemoryUpdated event has already been emitted.
    - A scheduled maintenance task (reindex_stale_memories) runs hourly
      and regenerates embeddings for any memory record whose embedding
      version is behind the field version.
    - If a field update is staged for confirmation (case "confirm") and
      the confirmation token expires (15 min TTL), the pending update is
    garbage-collected by a periodic task (expire_staged_memory_updates)
      and the memory reverts to its pre-request state. The user is not
      notified — the assumption is they chose not to confirm.


# 6. Event Processing Matrix

This section defines the complete processing pipeline for every domain event in the system. Each row describes a single event's journey from production through consumption, including queue routing, Celery task dispatch, retry and dead-letter handling, saga coordination, notification triggers, and analytics impact.

---

## 6.1 Event Processing Table

| Event | Producer | Consumers | Queue | Celery Task | Retry Policy | Dead Letter Queue | Saga Step | Notification Trigger | Analytics Impact |
|-------|----------|-----------|-------|-------------|--------------|-------------------|------------|---------------------|------------------|
| ConversationStarted | Conversation aggregate (on first message) | IntentDetector (application service), MemoryManager (short-term buffer init), WorkflowOrchestrator (trigger post-conversation-start rules) | queue:conversation.events | task:detect_intent (async intent classification), task:init_conversation_memory (warm Redis buffer) | Retry 3x, exponential backoff 1s-4s-16s, max jitter 500ms | DLQ:conversation.dead (TTL 7 days) | Saga:ConversationLifecycle — step 1/5 (start) | None (internal pipeline event) | Increment active_conversations gauge; emit conversation_started_latency histogram |
| ConversationEnded | Conversation aggregate (on archive/timeout) | MemoryManager (persist long-term summary), LeadScorer (assess lead quality from conversation), AnalyticsCollector | queue:conversation.events | task:summarize_conversation (LLM summarization), task:update_lead_score_from_conversation | Retry 3x, exponential backoff 2s-8s-32s | DLQ:conversation.dead (TTL 7 days) | Saga:ConversationLifecycle — step 5/5 (end) | None (aggregate state change) | Emit conversation_duration metric; tag session as ended for churn analysis |
| IntentDetected | IntentDetector service (receives ConversationStarted) | MessageRouter (route to appropriate agent), ContextBuilder (update conversation context), WorkflowTrigger (check intent-based workflow rules) | queue:intent.events | task:route_message_by_intent (dispatch to agent graph), task:build_context_prompt (update RAG context) | Retry 2x, fixed 5s interval — intents degrade quickly | DLQ:intent.dead (TTL 3 days) | Saga:ConversationLifecycle — step 2/5 (intent resolved) | None (internal routing decision) | Track intent_distribution histogram per intent type; feed intent to lead scoring model |
| MessageProcessed | AgentExecutor (after LLM responds) | MemoryManager (append to short-term buffer), WorkflowChecker (evaluate post-message workflow triggers), SentimentTracker | queue:message.events | task:append_to_memory_buffer (Redis list push), task:check_workflow_triggers (evaluate n8n rules) | Retry 3x, exponential backoff 1s-3s-9s | DLQ:message.dead (TTL 7 days) | Saga:ConversationLifecycle — step 3/5 (message handled) | None (internal pipeline event) | Record message_tokens_used, response_latency; emit per-agent response time |
| MeetingScheduled | Meeting aggregate (on schedule command) | CalendarSync (create calendar event), NotificationBuilder (build meeting confirmation), WorkflowOrchestrator (trigger post-schedule workflows), LeadScorer | queue:meeting.events | task:sync_calendar_event (Google/Outlook API), task:build_meeting_notification_payload, task:trigger_n8n_workflow (n8n webhook POST) | Retry 5x, exponential backoff 2s-4s-8s-16s-32s | DLQ:meeting.dead (TTL 14 days) | Saga:MeetingLifecycle — step 1/4 (scheduled) | NotificationSent (meeting confirmation email, push, Slack) | Emit meeting_scheduled counter; populate upcoming_meetings dashboard |
| MeetingConfirmed | Meeting aggregate (on participant accept) | ParticipantTracker (update RSVP status), NotificationBuilder (send confirmation to all participants), CalendarUpdater | queue:meeting.events | task:update_participant_rsvp (DB write), task:send_confirmation_notifications, task:update_calendar_invite | Retry 2x, fixed 10s | DLQ:meeting.dead (TTL 14 days) | Saga:MeetingLifecycle — step 2/4 (confirmed) | NotificationSent (confirmation to all participants) | Track meeting_acceptance_rate per organizer |
| MeetingCancelled | Meeting aggregate (on cancel command) | ParticipantNotifier (notify all participants), CalendarCleanup (remove calendar event), WorkflowTrigger (post-cancellation workflows), RefundProcessor | queue:meeting.events | task:notify_participants_cancellation, task:remove_calendar_event, task:trigger_cancellation_n8n_workflow | Retry 3x, exponential backoff 1s-5s-25s | DLQ:meeting.dead (TTL 14 days) | Saga:MeetingLifecycle — step 4/4 (cancelled, compensation) | NotificationSent (cancellation alert to all participants) | Emit meeting_cancelled counter; track cancellation_reason breakdown |
| MeetingFailed | Meeting infrastructure (transcription/recording error) | ErrorHandler (log failure), RetryOrchestrator (queue retry or abort), MonitoringAlert (PagerDuty if threshold exceeded) | queue:meeting.dead (direct DLQ on failure) | task:handle_meeting_failure (assess retry vs abort), task:escalate_meeting_failure (PagerDuty if >3 failures in 1h) | Retry 3x with Celery task retry, then DLQ | DLQ:meeting.dead (TTL 30 days — extended for forensic analysis) | Saga:MeetingLifecycle — step 3/4 (failed, triggers compensation) | NotificationSent (failure alert to organizer, ops channel) | Increment meeting_failure counter; tag by failure_reason; alert if rate > 5% |
| LeadCreated | Lead aggregate (on capture from form/API) | LeadEnricher (call Clearbit/Hunter), LeadScorer (calculate initial score), WorkflowTrigger (lead-capture workflows), DedupChecker | queue:lead.events | task:enrich_lead_external (3rd-party API enrichment), task:calculate_initial_score (ML scoring model), task:check_duplicate_leads | Retry 5x, exponential backoff 2s-4s-8s-16s-32s | DLQ:lead.dead (TTL 30 days) | Saga:LeadLifecycle — step 1/4 (captured) | NotificationSent (lead assigned notification to sales rep) | Emit lead_created counter; populate leads_funnel dashboard |
| LeadQualified | Lead aggregate (on score threshold or manual qualify) | LeadAssigner (auto-assign to sales rep), PipelineUpdater (move to qualified pipeline), WorkflowTrigger (qualified-lead workflows), SequenceEnroller | queue:lead.events | task:assign_lead_to_rep (round-robin / skill-based), task:update_crm_pipeline (Salesforce/HubSpot push) | Retry 3x, exponential backoff 2s-8s-32s | DLQ:lead.dead (TTL 30 days) | Saga:LeadLifecycle — step 2/4 (qualified) | NotificationSent (assignment notification + email to rep) | Emit lead_qualified counter; track qualification_time metric |
| LeadConverted | Lead aggregate (on convert command after deal closed) | CrmSync (push to CRM as closed-won), ContractGenerator (generate contract), AnalyticsFinalizer (finalize lead analytics), WorkflowTrigger | queue:lead.events | task:sync_to_crm_closed_won, task:generate_contract_document (PDF generation), task:trigger_post_conversion_n8n | Retry 5x, exponential backoff 1s-2s-4s-8s-16s | DLQ:lead.dead (TTL 30 days) | Saga:LeadLifecycle — step 4/4 (converted) | NotificationSent (conversion celebration to team Slack) | Emit lead_converted counter; compute conversion_rate; update revenue dashboard |
| MemoryUpdated | MemoryManager (on short-term buffer flush or long-term persist) | ContextBuilder (refresh active context), RAGIndexer (update vector index if semantic memory changed), ConversationSummarizer | queue:memory.events | task:refresh_context_window (rebuild agent prompt context), task:update_vector_embedding (if semantic memory) | Retry 2x, fixed 3s — memory staleness is acceptable | DLQ:memory.dead (TTL 1 day) | Saga:ConversationLifecycle — step 4/5 (memory synced) | None (internal state sync) | Track memory_update_latency; monitor memory_size per conversation |
| ConversationSummarized | MemoryManager (after summarization completes) | LongTermStore (persist summary to PostgreSQL), LeadScorer (update lead score from summary), AnalyticsCollector | queue:memory.events | task:store_conversation_summary (write to long-term DB), task:update_lead_from_summary (sentiment / intent extraction) | Retry 3x, exponential backoff 2s-10s-50s | DLQ:memory.dead (TTL 7 days) | Saga:ConversationLifecycle — step 5/5 (summarized) | None (internal persistence) | Emit conversation_summary_length; track summary_coverage ratio |
| WorkflowStarted | WorkflowExecution aggregate (on trigger) | StepExecutor (begin step 1 execution), StateTracker (record running state in Redis), QuotaManager (deduct from tenant quota) | queue:workflow.events | task:execute_workflow_step (generic step runner), task:update_workflow_state (Redis state write) | N/A (first attempt — subsequent failures use step-level retry) | N/A (failure handled at step level, not workflow level) | Saga:WorkflowLifecycle — step 1/3 (started) | None (until completion or failure) | Emit workflow_started counter; measure workflow_queue_wait_time |
| WorkflowCompleted | WorkflowExecution aggregate (on last step success) | OutputPersister (save final outputs), CallbackInvoker (call webhook callback if configured), NotificationBuilder | queue:workflow.events | task:persist_workflow_outputs (DB write + blob storage), task:invoke_completion_callback (HTTP POST), task:clear_workflow_state (Redis cleanup) | Retry 3x, exponential backoff 2s-8s-32s | DLQ:workflow.dead (TTL 14 days) | Saga:WorkflowLifecycle — step 3/3 (completed) | NotificationSent (completion alert if workflow is user-facing) | Emit workflow_completed counter; compute workflow_duration histogram |
| WorkflowFailed | WorkflowExecution aggregate (on unrecoverable step failure) | ErrorAggregator (collect failure context), CompensationCoordinator (start compensation saga), AlertingService (PagerDuty if critical) | queue:workflow.dead (direct DLQ) | task:aggregate_workflow_errors (roll up step failures), task:start_compensation_saga, task:escalate_to_oncall (PagerDuty) | Retry 3x with Celery task retry before DLQ escalation | DLQ:workflow.dead (TTL 30 days) | Saga:WorkflowLifecycle — step 3/3 (failed, start compensation) | NotificationSent (failure alert + escalation to on-call) | Emit workflow_failed counter; compute failure_rate per workflow_def; alert on threshold breach |
| WorkflowCompensated | CompensationCoordinator (after compensation saga executes) | StateRollback (restore pre-workflow state), AuditLogger (log full compensation trail), QuotaRefund (restore consumed quota) | queue:workflow.events | task:rollback_aggregate_states (call compensation handlers per affected aggregate), task:log_compensation_audit_trail, task:refund_tenant_quota | Retry 5x, exponential backoff 1s-2s-4s-8s-16s — compensations must eventually succeed | DLQ:workflow.dead (TTL 14 days) — manual intervention if compensation fails | Saga:WorkflowLifecycle — compensation complete | NotificationSent (compensation success alert to ops) | Track compensation_success_rate; measure compensation_duration |
| NotificationSent | Notification aggregate (on successful delivery to channel) | DeliveryTracker (mark delivery log as sent), AnalyticsCollector (record notification event), EngagementScorer | queue:notification.events | task:mark_notification_delivered (update delivery_log status), task:track_notification_analytics (write to analytics pipeline) | Retry 2x, fixed 5s — delivery status is informational | N/A (delivery status is not critical enough for DLQ) | None (notification is async side-effect) | N/A (this IS the notification outcome) | Emit notification_sent counter per channel; compute delivery_latency per provider |
| NotificationFailed | Notification aggregate (on channel delivery failure) | FailoverRouter (try alternate channel — e.g. email fallback after push failure), ErrorLogger (record failure reason), RateLimitChecker | queue:notification.dead (DLQ after all fallbacks exhausted) | task:handle_notification_failure (evaluate fallback channels), task:retry_alternate_channel, task:escalate_notification_failure (if all channels exhausted) | Retry 3x per channel, exponential backoff 2s-10s-50s, then fallback channel, then DLQ | DLQ:notification.dead (TTL 7 days) | None (notifications are not sagas) | NotificationSent (escalation alert to ops if all delivery channels failed) | Emit notification_failed counter per channel; track failure_reason distribution; alert if failure_rate > 10% |
| CircuitBreakerOpened | CircuitBreaker middleware (on consecutive provider failure threshold) | HealthChecker (mark provider degraded), ProviderManager (route traffic to fallback provider), AlertingService (immediate PagerDuty), RateLimiter (reduce throughput to failing provider) | queue:circuit-breaker.events (high-priority queue) | task:route_traffic_to_fallback (update provider routing table), task:schedule_circuit_half_open (set timer for half-open probe), task:notify_ops_team (PagerDuty + Slack) | N/A (circuit breaker is not retried — it opens once and transitions to half-open on timer) | N/A (circuit breaker state is managed in Redis, not queued) | N/A (cross-cutting concern, not a saga step) | NotificationSent (immediate PagerDuty + Slack to on-call) | Emit circuit_breaker_opened counter; track provider_unhealthy_seconds; alert on any occurrence |

---

## 6.2 Event Flow: ConversationStarted → IntentDetected → MessageProcessed

This chain is the core conversation lifecycle. It involves a saga, compensation paths for failures, and multiple retry layers.

    ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
    │ Saga: ConversationLifecycle                                                                 │
    │ Coordinator: ConversationSagaCoordinator (application layer)                                │
    │ Store: Redis key saga:{conversation_id}:state (hash: step, status, compensation_stack)      │
    ├─────────────────────────────────────────────────────────────────────────────────────────────┤
    │ Step 1/5: STARTED        → ConversationStarted published                                   │
    │ Step 2/5: INTENT_RESOLVED → IntentDetected published                                       │
    │ Step 3/5: MESSAGE_HANDLED → MessageProcessed published                                     │
    │ Step 4/5: MEMORY_SYNCED  → MemoryUpdated published                                         │
    │ Step 5/5: SUMMARIZED     → ConversationSummarized published (on conversation end)          │
    └─────────────────────────────────────────────────────────────────────────────────────────────┘

    Participant: API Gateway
    Participant: Conversation Aggregate
    Participant: ConversationSagaCoordinator
    Participant: IntentDetector Service
    Participant: MessageRouter
    Participant: Agent Executor
    Participant: MemoryManager
    Participant: n8n Workflow Engine

    Sequence Diagram:

        API Gateway               Conv Aggregate           SagaCoordinator         IntentDetector          MessageRouter          Agent Executor         MemoryManager            n8n
            │                           │                        │                       │                       │                       │                       │                   │
            │  POST /api/v1/...          │                        │                       │                       │                       │                       │                   │
            │──────────────────────────▶│                        │                       │                       │                       │                       │                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │  ConversationStarted   │                       │                       │                       │                       │                   │
            │                           │───────────────────────▶│                       │                       │                       │                       │                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │  Saga-Init(step=1)    │                       │                       │                       │                   │
            │                           │                        │───┐                   │                       │                       │                       │                   │
            │                           │                        │   │ Redis: saga state  │                       │                       │                       │                   │
            │                           │                        │◄──┘  = STARTED        │                       │                       │                       │                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │  Enqueue IntentDetect │                       │                       │                       │                   │
            │                           │                        │───────────────────────▶│                       │                       │                       │                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │     ┌──[Retry Policy]──┘                       │                       │                       │                   │
            │                           │                        │     │ 3 attempts                                   │                       │                       │                   │
            │                           │                        │     │ 1s -> 4s -> 16s                                │                       │                       │                   │
            │                           │                        │     │ jitter: 500ms                               │                       │                       │                   │
            │                           │                        │     └─────────────────────────────────────────────▶│                       │                       │                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │                       │  IntentDetected        │                       │                       │                   │
            │                           │                        │                       │◄───────────────────────│                       │                       │                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │  Saga-Update(step=2)  │                       │                       │                       │                   │
            │                           │                        │───┐                   │                       │                       │                       │                   │
            │                           │                        │   │ Redis: saga state  │                       │                       │                       │                   │
            │                           │                        │◄──┘  = INTENT_RESOLVED│                       │                       │                       │                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │  Route message        │                       │                       │                       │                   │
            │                           │                        │───────────────────────────────────────────────▶│                       │                       │                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │                       │                       │  Agent Execute         │                       │                   │
            │                           │                        │                       │                       │───────────────────────▶│                       │                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │                       │                       │     ┌──[Retry Policy]──┘                       │                   │
            │                           │                        │                       │                       │     │ 3 attempts                                    │                   │
            │                           │                        │                       │                       │     │ 1s -> 3s -> 9s                                │                   │
            │                           │                        │                       │                       │     └──────────────────────────────────────────▶│                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │                       │                       │  MessageProcessed      │                       │                   │
            │                           │                        │                       │                       │◄───────────────────────│                       │                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │  Saga-Update(step=3)  │                       │                       │                       │                   │
            │                           │                        │───┐                   │                       │                       │                       │                   │
            │                           │                        │   │ Redis: saga state  │                       │                       │                       │                   │
            │                           │                        │◄──┘  = MESSAGE_HANDLED│                       │                       │                       │                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │  Enqueue MemoryUpdate │                       │                       │                       │                   │
            │                           │                        │───────────────────────────────────────────────────────────────────────────▶│                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │                       │                       │                       │  MemoryUpdated        │                   │
            │                           │                        │                       │                       │                       │◄──────────────────────│                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │  Saga-Update(step=4)  │                       │                       │                       │                   │
            │                           │                        │───┐                   │                       │                       │                       │                   │
            │                           │                        │   │ Redis: saga state  │                       │                       │                       │                   │
            │                           │                        │◄──┘  = MEMORY_SYNCED  │                       │                       │                       │                   │
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │  [If n8n workflow     │                       │                       │                       │                   │
            │                           │                        │   trigger configured] │                       │                       │                       │                   │
            │                           │                        │─────────────────────────────────────────────────────────────────────────────────────────────▶│
            │                           │                        │                       │                       │                       │                       │                   │
            │                           │                        │                       │                       │                       │                       │  HTTP POST /webhook │
            │                           │                        │                       │                       │                       │                       │◄──────────────────▶│

    Compensation Path (on failure at any step):

        ┌───────────────────────────────────────────────────────────────────────────────────────────────┐
        │ Failure at Step 2 (Intent Detection fails all retries):                                      │
        │   1. SagaCoordinator detects step=2 timeout after 3 retries                                  │
        │   2. SagaCoordinator pushes CompensationCommand("undo-conversation-start") to queue:compensation │
        │   3. CompensationHandler pops:                                                               │
        │       a. MemoryManager: rollback short-term buffer (delete buffered messages)                │
        │       b. Conversation Aggregate: revert state to PENDING (not STARTED)                       │
        │       c. Publish ConversationStartReverted domain event                                      │
        │   4. SagaCoordinator marks saga status=COMPENSATED in Redis                                  │
        │   5. NotificationTrigger: send failure alert to ops channel                                  │
        │                                                                                              │
        │ Failure at Step 3 (Agent execution fails all retries):                                       │
        │   1. SagaCoordinator detects step=3 timeout                                                  │
        │   2. SagaCoordinator pushes CompensationCommand("undo-intent-resolution") to queue:compensation  │
        │   3. CompensationHandler pops:                                                               │
        │       a. IntentDetector: clear cached intent classification for this message                 │
        │       b. MessageRouter: release agent session state                                          │
        │       c. MemoryManager: no rollback needed (intent buffer is ephemeral)                      │
        │       d. Conversation Aggregate: set message_pending flag to allow re-route                  │
        │   4. SagaCoordinator publishes CompensationCompleted event                                    │
        │   5. Queue retry of ConversationStarted -> intent re-detection on next attempt                │
        └───────────────────────────────────────────────────────────────────────────────────────────────┘

---

## 6.3 Event Flow: MeetingScheduled -> NotificationSent -> n8n Workflow Trigger

This chain demonstrates calendar integration, multi-channel notification fan-out, and external workflow automation through n8n.

    ┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
    │ Saga: MeetingLifecycle                                                                               │
    │ Coordinator: MeetingSagaCoordinator (application layer)                                              │
    │ Store: Redis key saga:meeting:{meeting_id}:state (hash: step, status, escalation_level)              │
    ├───────────────────────────────────────────────────────────────────────────────────────────────────────┤
    │ Step 1/4: SCHEDULED     -> MeetingScheduled published  -> calendar sync + notification + n8n trigger  │
    │ Step 2/4: CONFIRMED     -> MeetingConfirmed published  -> RSVP update + confirmation emails           │
    │ Step 3/4: FAILED        -> MeetingFailed published     -> compensation / retry                         │
    │ Step 4/4: CANCELLED     -> MeetingCancelled published  -> rollback calendar + notify participants     │
    └───────────────────────────────────────────────────────────────────────────────────────────────────────┘

    Sequence Diagram:

        Meeting Aggregate     MeetingSagaCoordinator     CalendarSync Service    Notification Builder         n8n Webhook              Lead Scorer
                │                        │                       │                       │                       │                       │
                │  MeetingScheduled      │                       │                       │                       │                       │
                │───────────────────────▶│                       │                       │                       │                       │
                │                        │                       │                       │                       │                       │
                │                        │  Saga-Init(step=1)    │                       │                       │                       │
                │                        │───┐                   │                       │                       │                       │
                │                        │   │ Redis: state      │                       │                       │                       │
                │                        │◄──┘  = SCHEDULED     │                       │                       │                       │
                │                        │                       │                       │                       │                       │
                │                        │  ┌── Fan-out ──┐      │                       │                       │                       │
                │                        │  │             │      │                       │                       │                       │
                │                        │  ▼             ▼      │                       │                       │                       │
                │                        │                       │                       │                       │                       │
                │  ┌──[Branch 1:──────┐  │  Enqueue calendar     │                       │                       │                       │
                │  │  Calendar Sync   │──│──────────────────────▶│                       │                       │                       │
                │  │  Retry: 5x,     │  │                       │                       │                       │                       │
                │  │  2s->4s->8s->16s->32s│  │                       │  HTTP POST /calendar  │                       │                       │
                │  └─────────────────┘  │                       │──────────────────────▶│ (Google/Outlook API)  │                       │
                │                        │                       │                       │                       │                       │
                │                        │                       │  CalendarCreated      │                       │                       │
                │                        │                       │◄──────────────────────│                       │                       │
                │                        │                       │                       │                       │                       │
                │  ┌──[Branch 2:──────┐  │  Enqueue notification │                       │                       │                       │
                │  │  Notification    │──│─────────────────────────────────────────────▶│                       │                       │
                │  │  Retry: 3x per  │  │                       │                       │                       │                       │
                │  │  channel, then   │  │                       │                       │  Build payload        │                       │
                │  │  fallback, then  │  │                       │                       │───┐                   │                       │
                │  │  DLQ: 7 days    │  │                       │                       │   │ template render    │                       │
                │  └─────────────────┘  │                       │                       │◄──┘ + channel routing│                       │
                │                        │                       │                       │                       │                       │
                │  ┌──[Branch 3:──────┐  │                       │                       │  NotificationSent     │                       │
                │  │  n8n Trigger     │  │                       │                       │───┐                   │                       │
                │  │  Retry: 3x,     │  │                       │                       │   │ delivery log       │                       │
                │  │  1s->3s->9s       │  │  Enqueue n8n trigger  │                       │◄──┘ update             │                       │
                │  └─────────────────┘──│────────────────────────────────────────────────────────────────────▶│                       │
                │                        │                       │                       │                       │                       │
                │  ┌──[Branch 4:──────┐  │                       │                       │                       │  HTTP POST /webhook   │
                │  │  Lead Scoring    │──│──────────────────────────────────────────────────────────────────────────────────────────▶│
                │  │  Retry: 3x,     │  │                       │                       │                       │  /meeting-scheduled   │
                │  │  2s->8s->32s      │  │                       │                       │                       │──────────────────────▶│
                │  └─────────────────┘  │                       │                       │                       │                       │
                │                        │                       │                       │                       │  [n8n Workflow Runs]  │
                │                        │                       │                       │                       │  ├─ Create Calendar   │
                │                        │                       │                       │                       │  │  Event (Google)    │
                │                        │                       │                       │                       │  ├─ Send Slack        │
                │                        │                       │                       │                       │  │  Notification      │
                │                        │                       │                       │                       │  ├─ Update CRM        │
                │                        │                       │                       │                       │  │  Record (optional) │
                │                        │                       │                       │                       │  └─ Log to Google    │
                │                        │                       │                       │                       │     Sheets (analytics)│
                │                        │                       │                       │                       │                       │
                │                        │                       │                       │                       │  200 OK               │
                │                        │                       │                       │                       │◄──────────────────────│
                │                        │                       │                       │                       │                       │
                │                        │                       │                       │                       │                       │
                │                        │                       │                       │                       │  Lead score update    │
                │                        │                       │                       │                       │◄──────────────────────│
                │                        │                       │                       │                       │                       │
                │                        │  Saga-Update(step=1   │                       │                       │                       │
                │                        │  = SCHEDULED,         │                       │                       │                       │
                │                        │  status=COMPLETED)    │                       │                       │                       │
                │                        │───┐                   │                       │                       │                       │
                │                        │   │ Redis: all 4      │                       │                       │                       │
                │                        │◄──┘  branches done   │                       │                       │                       │

    NotificationSent Delivery Detail (Branch 2 internals):

        ┌──────────────────────────────────────────────────────────────┐
        │ NotificationBuilder receives MeetingScheduled event:         │
        │                                                             │
        │   1. Resolve delivery preferences from UserProfile aggregate│
        │      a. user_preferences.notifications.meeting_confirmation │
        │                                                             │
        │   2. Build notification payload per channel:                 │
        │      a. IN-APP: { title, body, action_url, metadata }       │
        │      b. PUSH:   { token, title, body, badge_count }         │
        │      c. EMAIL:  { to, subject, html_body, calendar_ics }    │
        │      d. SLACK:  { webhook_url, blocks, channel }            │
        │                                                             │
        │   3. For each enabled channel, enqueue to:                   │
        │      a. queue:notification.delivery.in-app                   │
        │      b. queue:notification.delivery.push  (FCM/APNs)        │
        │      c. queue:notification.delivery.email (SES/SendGrid)    │
        │      d. queue:notification.delivery.slack (webhook POST)    │
        │                                                             │
        │   4. Celery tasks per channel (independent, parallel):       │
        │      a. task:deliver_in_app_notification   - Retry 3x, 1s-3s-9s         │
        │      b. task:deliver_push_notification     - Retry 3x, 2s-10s-50s       │
        │      c. task:deliver_email_notification    - Retry 5x, 5s-25s-125s      │
        │      d. task:deliver_slack_notification    - Retry 2x, 3s-9s            │
        │                                                             │
        │   5. On channel failure: fallback to next channel            │
        │      a. PUSH fails -> try EMAIL (if configured)              │
        │      b. EMAIL fails -> try SLACK (if configured)             │
        │      c. All fail -> publish NotificationFailed -> DLQ         │
        │                                                             │
        │   6. On success: publish NotificationSent event             │
        │      -> AnalyticsCollector records notification_sent metric  │
        │                                                             │
        │   7. If all channels fail after fallbacks:                   │
        │      -> NotificationFailed -> queue:notification.dead         │
        │      -> Retry entire batch after 5 minutes (max 3 batch      │
        │        retries)                                             │
        │      -> Escalate to ops via PagerDuty if batch exceeds       │
        │        notification circuit breaker threshold (3 failures   │
        │        in 1 hour per user)                                  │
        └──────────────────────────────────────────────────────────────┘

    n8n Workflow Definition (Branch 3 detail):

        ┌──────────────────────────────────────────────────────────────┐
        │ n8n Webhook: POST /webhook/meeting-scheduled                │
        │                                                             │
        │ Payload:                                                    │
        │   {                                                         │
        │     "event": "MeetingScheduled",                            │
        │     "meeting_id": "m_abc123",                               │
        │     "organizer_id": "u_xyz789",                             │
        │     "title": "Sprint Planning",                             │
        │     "start_time": "2026-07-01T09:00:00Z",                   │
        │     "end_time": "2026-07-01T10:00:00Z",                    │
        │     "participants": ["u_abc", "u_def", "u_ghi"],           │
        │     "conversation_id": "c_12345",                           │
        │     "metadata": {                                           │
        │       "source": "slack-command",                            │
        │       "workflow_def_id": "wf_sprint_001"                    │
        │     }                                                       │
        │   }                                                         │
        │                                                             │
        │ Workflow Nodes:                                             │
        │                                                             │
        │   1. [Webhook Trigger] <- Receives MeetingScheduled          │
        │          │                                                  │
        │          ▼                                                  │
        │   2. [Set] Transform: compute end_time if missing           │
        │          │                                                  │
        │          ├──────────────────────────────────┐               │
        │          ▼                                  ▼              │
        │   3a. [Google Calendar]               3b. [Slack]          │
        │       Create Event                       Send Message      │
        │       Summary: "Sprint Planning"         Channel: #meetings │
        │       Start: 2026-07-01T09:00:00Z        Text: "Meeting     │
        │       End:   2026-07-01T10:00:00Z        scheduled: Sprint  │
        │       Attendees: [participants]          Planning @ 9 AM   │
        │          │                                  │              │
        │          ▼                                  ▼              │
        │   4a. [Set] Output: calendar_event_id   4b. [Set] Output:  │
        │       = returned id                         slack_ts =    │
        │          │                                  returned ts   │
        │          ▼                                  │              │
        │   5. [Merge] Combine all branch outputs                    │
        │          │                                                  │
        │          ▼                                                  │
        │   6. [Respond] 200 OK to webhook caller                     │
        │          │                                                  │
        │          ▼                                                  │
        │   7. [HTTP Request] PATCH /internal/meetings/{id}           │
        │       Body: { "external_refs": {                            │
        │         "calendar_event_id": "...",                         │
        │         "slack_message_ts": "..."                           │
        │       }}                                                    │
        │                                                             │
        │ Error Handling:                                             │
        │   - If Google Calendar returns 429 (rate limit):            │
        │     Wait 60s (n8n error node), retry up to 3 times          │
        │   - If Slack returns error: skip Slack node, log warning    │
        │   - If both fail: n8n posts to error webhook ->             │
        │     queue:workflow.dead -> manual review                    │
        └──────────────────────────────────────────────────────────────┘

---

## 6.4 Retry Policy Reference

| Policy Name | Strategy | Max Attempts | Backoff | Jitter | Applicable Events |
|-------------|----------|--------------|---------|--------|-------------------|
| default_fast | Exponential | 3 | 1s, 3s, 9s | 250ms | MessageProcessed, ConversationStarted, IntentDetected |
| default_medium | Exponential | 3 | 2s, 8s, 32s | 500ms | ConversationEnded, ConversationSummarized, MeetingCancelled, WorkflowCompleted, LeadQualified, MemoryUpdated |
| default_slow | Exponential | 5 | 2s, 4s, 8s, 16s, 32s | 1s | MeetingScheduled, LeadCreated, LeadConverted, WorkflowCompensated |
| calendar_external | Exponential | 5 | 2s, 4s, 8s, 16s, 32s | 500ms | MeetingScheduled (calendar sync branch) |
| notification_push | Exponential | 3 | 2s, 10s, 50s | 1s | NotificationSent (push channel) |
| notification_email | Exponential | 5 | 5s, 25s, 125s | 2s | NotificationSent (email channel) |
| notification_slack | Fixed | 2 | 3s, 9s | 100ms | NotificationSent (slack channel) |
| notification_fallback | Fixed | 3 | 5min (batch retry) | 0s | NotificationFailed (batch retry after all channels exhausted) |
| workflow_step | Exponential | 3 | 2s, 8s, 32s | 500ms | WorkflowStarted (step execution) |
| lead_external_api | Exponential | 5 | 2s, 4s, 8s, 16s, 32s | 1s | LeadCreated (enrichment API) |

---

## 6.5 Dead Letter Queue Summary

| Dead Letter Queue | TTL | Events Routed | Manual Replay Action | Automatic Replay |
|-------------------|-----|---------------|---------------------|------------------|
| DLQ:conversation.dead | 7 days | ConversationStarted, ConversationEnded, MessageProcessed | POST /internal/admin/dlq/replay/conversation | Celery beat task: replay_dead_letters (daily, max 3 replays) |
| DLQ:intent.dead | 3 days | IntentDetected | POST /internal/admin/dlq/replay/intent | Celery beat task: replay_intent_dead_letters (every 6h, max 2 replays) |
| DLQ:meeting.dead | 14 days | MeetingScheduled, MeetingConfirmed, MeetingCancelled | POST /internal/admin/dlq/replay/meeting | Manual only (calendar side effects require human approval) |
| DLQ:meeting.dead (extended) | 30 days | MeetingFailed | POST /internal/admin/dlq/replay/meeting-failed | Manual only (forensic analysis before replay) |
| DLQ:lead.dead | 30 days | LeadCreated, LeadQualified, LeadConverted | POST /internal/admin/dlq/replay/lead | Celery beat task: replay_lead_dead_letters (daily, max 2 replays) |
| DLQ:memory.dead | 1 day | MemoryUpdated, ConversationSummarized | POST /internal/admin/dlq/replay/memory | Automatic on next conversation activity (lazy replay) |
| DLQ:workflow.dead | 14 days | WorkflowCompleted, WorkflowCompensated | POST /internal/admin/dlq/replay/workflow | Manual only (workflow side effects may be destructive on replay) |
| DLQ:workflow.dead (extended) | 30 days | WorkflowFailed | POST /internal/admin/dlq/replay/workflow-failed | Manual only (requires failure analysis) |
| DLQ:notification.dead | 7 days | NotificationFailed | POST /internal/admin/dlq/replay/notification | Celery beat task: replay_notification_dead_letters (every hour, max 5 replays per notification) |

---

## 6.6 Dead Letter Queue Architecture

    ┌─────────────────────────────────────────────────────────────────────────┐
    │ Dead Letter Queue Architecture                                          │
    │                                                                         │
    │   Primary Queue          Dead Letter Queue        Replay Mechanism      │
    │   ┌─────────────┐       ┌─────────────────┐      ┌─────────────────┐   │
    │   │ queue:conv   │──────▶│ DLQ:conversation │─────▶│ beat:replay     │   │
    │   │ .events      │       │ .dead (TTL 7d)   │      │ (daily, max 3)  │   │
    │   └─────────────┘       └─────────────────┘      └─────────────────┘   │
    │                                                                         │
    │   ┌─────────────┐       ┌─────────────────┐      ┌─────────────────┐   │
    │   │ queue:intent │──────▶│ DLQ:intent.dead  │─────▶│ beat:replay     │   │
    │   │ .events      │       │ (TTL 3d)         │      │ (every 6h,     │   │
    │   └─────────────┘       └─────────────────┘      │  max 2)         │   │
    │                                                  └─────────────────┘   │
    │   ┌─────────────┐       ┌─────────────────┐                            │
    │   │ queue:meeting│──────▶│ DLQ:meeting.dead │      ┌─────────────────┐ │
    │   │ .events      │       │ (TTL 14d / 30d)  │─────▶│ manual replay   │ │
    │   └─────────────┘       └─────────────────┘      │ (admin API)      │ │
    │                                                  └─────────────────┘ │
    │   ┌─────────────┐       ┌─────────────────┐      ┌─────────────────┐   │
    │   │ queue:lead   │──────▶│ DLQ:lead.dead    │─────▶│ beat:replay     │   │
    │   │ .events      │       │ (TTL 30d)        │      │ (daily, max 2)  │   │
    │   └─────────────┘       └─────────────────┘      └─────────────────┘   │
    │                                                                         │
    │   ┌─────────────┐       ┌─────────────────┐      ┌─────────────────┐   │
    │   │ queue:memory  │──────▶│ DLQ:memory.dead │─────▶│ lazy replay     │   │
    │   │ .events      │       │ (TTL 1d)         │      │ (on next       │   │
    │   └─────────────┘       └─────────────────┘      │  activity)      │   │
    │                                                  └─────────────────┘   │
    │   ┌─────────────┐       ┌─────────────────┐      ┌─────────────────┐   │
    │   │ queue:workflow│──────▶│ DLQ:workflow.dead│─────▶│ manual replay   │   │
    │   │ .events      │       │ (TTL 14d / 30d)  │      │ (admin API)      │   │
    │   └─────────────┘       └─────────────────┘      └─────────────────┘   │
    │                                                                         │
    │   ┌─────────────┐       ┌─────────────────┐      ┌─────────────────┐   │
    │   │ queue:notif  │──────▶│ DLQ:notification │─────▶│ beat:replay     │   │
    │   │ .events      │       │ .dead (TTL 7d)  │      │ (every 1h,     │   │
    │   └─────────────┘       └─────────────────┘      │  max 5 per notif)│   │
    │                                                  └─────────────────┘   │
    │                                                                         │
    │   ┌─────────────────────────────────────────────────────────────────┐   │
    │   │ Monitoring: alert on any dead letter queue depth > 100 messages │   │
    │   │ Alert channel: PagerDuty + Slack #ops-alerts                    │   │
    │   │ Dashboard: Grafana panel showing per-queue depth, replay count, │   │
    │   │   and oldest message age                                        │   │
    │   └─────────────────────────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────────────────────────┘

---

## 6.7 Event Correlation ID Strategy

Every event across the entire pipeline carries a correlation_id that is propagated from the root HTTP request (or background job trigger) through all downstream events, queues, Celery tasks, sagas, notifications, and n8n webhooks.

    Correlation ID propagation:
        HTTP Request (X-Correlation-ID header)
            │
            ▼
        Command Handler ──────────────────────────────────► Domain Event
            │                                                   │
            ▼                                                   ▼
        Application Service ──► Queue (correlation_id in message headers)
            │                                                   │
            ▼                                                   ▼
        Celery Task (correlation_id in task kwargs) ─────► Saga Coordinator
            │                                                   │
            ▼                                                   ▼
        n8n Webhook (correlation_id in payload) ──────────► Notification
            │                                                   │
            ▼                                                   ▼
        Logs (structured logging key: correlation_id) ───► Metrics (tag: correlation_id)
            │                                                   │
            ▼                                                   ▼
        Traces (OpenTelemetry span attribute: correlation_id)

    This enables end-to-end tracing of any event through the entire processing pipeline,
    from HTTP request -> domain logic -> queue -> Celery -> saga -> notification -> n8n workflow.

---

## 6.8 Event Catalog Summary

| # | Event | Type | Priority | Avg Throughput (per min) | Peak Throughput | Avg Latency (P50) | P99 Latency | Data Retention |
|---|-------|------|----------|--------------------------|-----------------|-------------------|-------------|----------------|
| 1 | ConversationStarted | Domain | High | 120 | 600 | 200ms | 1.5s | 90 days |
| 2 | ConversationEnded | Domain | Low | 60 | 300 | 500ms | 3s | 90 days |
| 3 | IntentDetected | Domain | High | 120 | 600 | 300ms | 2s | 30 days |
| 4 | MessageProcessed | Domain | High | 480 | 2400 | 2s | 15s | 90 days |
| 5 | MeetingScheduled | Domain | Medium | 20 | 100 | 500ms | 3s | 365 days |
| 6 | MeetingConfirmed | Domain | Medium | 15 | 80 | 300ms | 2s | 365 days |
| 7 | MeetingCancelled | Domain | Medium | 5 | 30 | 400ms | 2.5s | 365 days |
| 8 | MeetingFailed | Domain | Critical | 2 | 20 | 1s | 10s | 365 days |
| 9 | LeadCreated | Domain | High | 30 | 200 | 300ms | 2s | 730 days |
| 10 | LeadQualified | Domain | High | 15 | 100 | 400ms | 3s | 730 days |
| 11 | LeadConverted | Domain | High | 5 | 30 | 500ms | 4s | 730 days |
| 12 | MemoryUpdated | Domain | Low | 480 | 2400 | 100ms | 1s | 7 days |
| 13 | ConversationSummarized | Domain | Low | 60 | 300 | 5s | 30s | 365 days |
| 14 | WorkflowStarted | Integration | Medium | 40 | 200 | 300ms | 2s | 90 days |
| 15 | WorkflowCompleted | Integration | Medium | 35 | 180 | 500ms | 4s | 90 days |
| 16 | WorkflowFailed | Integration | Critical | 5 | 30 | 2s | 20s | 180 days |
| 17 | WorkflowCompensated | Integration | Critical | 3 | 15 | 3s | 25s | 180 days |
| 18 | NotificationSent | Integration | Low | 200 | 1000 | 200ms | 1s | 30 days |
| 19 | NotificationFailed | Integration | Medium | 10 | 50 | 1s | 10s | 30 days |
| 20 | CircuitBreakerOpened | Infrastructure | Critical | 0.1 | 5 | 100ms | 500ms | 90 days |

# 7. API Ownership Matrix

For every endpoint, this table defines the full ownership chain from HTTP through application service, repository, events, infrastructure (Redis, Database, Celery), and cross-cutting concerns (Authorization, Rate Limit, Validation, Error Types, Response DTO).

| Endpoint | Controller | Application Service | Repository | Events | Redis | Database | Celery | Authorization | Rate Limit | Validation | Error Types | Response DTO |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| POST /chat/message | ChatController | MessageProcessingService | ConversationRepository, MemoryRepository, UserProfileRepository | MessageReceived, IntentClassified, ToolExecutionRequested, MemoryUpdated, ResponseGenerated | conversation:{id}:lock (lock), conversation:{id}:recent (cache), user:{id}:rate-limit:{ep} (sliding window) | conversations, conversation_messages, memory_fields | process_message_async (LLM inference, tool execution, response generation) | Session token + ParticipantValidator (must be conversation participant) | 30 req/min per user, 200 req/min per tenant | MessagePayloadValidator, ConversationActiveValidator, ParticipantValidator, RateLimitValidator | 400 (validation), 404 (conversation not found), 409 (archived), 429 (rate limit), 500 (LLM failure) | MessageResponse (streamed SSE or complete JSON) |
| POST /chat/start | ChatController | ConversationService | ConversationRepository, UserProfileRepository | ConversationCreated, ParticipantAdded | conversation:{id}:state (init state), user:{id}:active-conversations (sorted set) | conversations, conversation_participants | start_conversation_notify (new-conversation notification) | Session token (any authenticated user) | 10 req/min per user | CreateConversationValidator, ParticipantLimitValidator, TenantQuotaValidator | 400 (validation), 422 (participant limit), 429 (rate limit), 500 | ConversationResponse (id, participants, created_at) |
| POST /chat/resume | ChatController | ConversationService | ConversationRepository, MemoryRepository | ConversationResumed | conversation:{id}:state (read), conversation:{id}:recent (cache warm), memory:{conv}:context (context reload) | conversations, conversation_messages, memory_fields | restore_conversation_context (rebuild agent context window) | Session token + ParticipantValidator | 20 req/min per user | ConversationExistsValidator, ConversationArchivedValidator, ParticipantValidator | 400 (validation), 404 (not found), 410 (deleted), 429 (rate limit) | ConversationResumeResponse (recent messages, memory context, state) |
| POST /chat/archive | ChatController | ConversationService | ConversationRepository | ConversationArchived | conversation:{id}:state (set archived), conversation:{id}:recent (del or TTL reduce) | conversations (state = archived) | expire_conversation_cache (Redis cleanup, long-term summary generation) | Session token + PermissionValidator (owner or admin) | 5 req/min per user | ConversationExistsValidator, AlreadyArchivedValidator, PermissionValidator | 400 (validation), 403 (forbidden), 404 (not found), 409 (already archived) | ArchiveResponse (archived_at, message_count) |
| GET /chat/{id}/summary | ChatController | SummaryService | ConversationRepository, MemoryRepository, KnowledgeDocumentRepository | SummaryGenerated, SummarySaved | conversation:{id}:summary (cache, TTL 1h) | conversation_messages (aggregated), knowledge_documents (persisted summary) | generate_conversation_summary (LLM summarization) | Session token + ParticipantValidator | 10 req/min per user | ConversationExistsValidator, SummaryPolicyValidator, TokenLimitValidator | 404 (not found), 422 (too long), 429 (rate limit), 503 (LLM unavailable) | SummaryResponse (summary_text, key_points, token_count) |
| GET /conversations/{id} | ConversationController | ConversationService | ConversationRepository | None (read-only) | conversation:{id}:recent (cache, TTL 1h), conversation:{id}:state (hash) | conversations, conversation_messages | None | Session token + ParticipantValidator | 60 req/min per user | ConversationExistsValidator (404 if missing) | 404 (not found), 429 (rate limit) | ConversationResponse |
| GET /conversations | ConversationController | ConversationService | ConversationRepository | None (read-only) | user:{id}:active-conversations (sorted set, TTL 5min) | conversations WHERE participant = user_id | None | Session token (any authenticated user) | 30 req/min per user | PaginationValidator, FilterValidator | 400 (invalid pagination), 429 (rate limit) | ConversationListResponse |
| GET /conversations/{id}/state | ConversationController | ConversationService | ConversationRepository | None (read-only) | conversation:{id}:state (hash, TTL = conversation duration + 1h) | conversations (state column) | None | Session token + ParticipantValidator | 120 req/min per user (high-frequency poll) | ConversationExistsValidator | 404 (not found), 429 (rate limit) | ConversationStateResponse |
| POST /meetings/schedule | MeetingController | MeetingService | MeetingRepository, UserProfileRepository | MeetingScheduled | meeting:availability:{date}:{user} (bitmap invalidation), meeting:slot-locks:{date} (slot reservation) | meetings, meeting_participants | send_meeting_notifications (calendar invites, push, email) | Session token (any authenticated user) | 10 req/min per user | MeetingRequestValidator, AvailabilityValidator, ParticipantConflictValidator, TimeSlotValidator | 400 (validation), 409 (slot conflict), 422 (time policy), 429 (rate limit) | MeetingResponse (id, time, participants, status) |
| POST /meetings/cancel | MeetingController | MeetingService | MeetingRepository | MeetingCancelled | meeting:{id}:state (set cancelled), meeting:availability:{date}:{user} (bitmap rebuild) | meetings (state = cancelled) | notify_cancellation (participant notifications, calendar cleanup) | Session token + PermissionValidator (organizer or admin) | 5 req/min per user | MeetingExistsValidator, CancelPolicyValidator, PermissionValidator | 403 (forbidden), 404 (not found), 409 (already ended), 429 (rate limit) | CancelResponse (cancelled_at, refund_status) |
| POST /meetings/reschedule | MeetingController | MeetingService | MeetingRepository | MeetingRescheduled | meeting:availability:{date}:{user} (bitmap rebuild for old + new slots) | meetings (start_time, end_time, state) | notify_reschedule (participant notifications, calendar update) | Session token + PermissionValidator (organizer or admin) | 5 req/min per user | MeetingExistsValidator, NewTimeSlotValidator, ParticipantConflictValidator, ReschedulePolicyValidator | 400 (validation), 403 (forbidden), 404 (not found), 409 (conflict), 429 (rate limit) | MeetingResponse (updated time, status) |
| POST /meetings/confirm | MeetingController | MeetingService | MeetingRepository | MeetingConfirmed, ParticipantConfirmed | meeting:{id}:state (update confirmation count) | meetings (state if all confirmed), meeting_participants (rsvp_status) | confirm_meeting_reminder (post-confirmation reminders) | Session token + ParticipantValidator (must be invited participant) | 10 req/min per user | MeetingExistsValidator, ConfirmationDeadlineValidator, ParticipantResponseValidator | 400 (validation), 404 (not found), 410 (expired), 429 (rate limit) | ConfirmationResponse (confirmed_participants, status) |
| GET /meetings/{id} | MeetingController | MeetingService | MeetingRepository | None (read-only) | meeting:{id}:state (hash, TTL = meeting duration + 1h) | meetings, meeting_participants | None | Session token + ParticipantValidator | 60 req/min per user | MeetingExistsValidator | 404 (not found), 429 (rate limit) | MeetingResponse |
| GET /meetings | MeetingController | MeetingService | MeetingRepository | None (read-only) | user:{id}:meetings (sorted set, TTL 2min) | meetings JOIN meeting_participants | None | Session token (any authenticated user) | 30 req/min per user | PaginationValidator, DateFilterValidator | 400 (invalid filter), 429 (rate limit) | UserMeetingsResponse |
| GET /meetings/availability | MeetingController | MeetingService | MeetingRepository | None (read-only) | meeting:availability:{date}:{user} (bitmap, TTL 30s), meeting:slot-locks:{date} (sorted set) | meetings (existing bookings for day) | None | Session token (any authenticated user) | 60 req/min per user | DateValidator, TimezoneValidator | 400 (invalid date), 429 (rate limit) | MeetingAvailabilityResponse |
| POST /leads/create | LeadController | LeadService | LeadRepository, UserProfileRepository | LeadCaptured | lead:capture:dedup:{email_hash} (TTL 24h, dedup), lead:score-queue (sorted set, score update) | leads, lead_interactions | enrich_lead_with_data (Clearbit/Hunter), score_lead (ML scoring) | Session token or API key (form submission) | 20 req/min per IP, 100 req/min per tenant | EmailUniquenessValidator, RequiredFieldValidator, DuplicateDetectionValidator, TenantQuotaValidator | 400 (validation), 409 (duplicate, returns existing), 422 (quota exceeded), 429 (rate limit) | LeadResponse (id, score, enrichment_status) |
| PUT /leads/{id}/qualify | LeadController | LeadService | LeadRepository | LeadQualified, LeadAssigned | lead:{id}:lock (lock, prevent double-scoring), lead:score-queue (sorted set, score update) | leads (score, tier, qualified_at), lead_scores | score_lead_batch (batch ML scoring), notify_lead_assignment (rep notification) | Session token + PermissionValidator (sales rep or admin) | 10 req/min per user | LeadExistsValidator, AlreadyQualifiedValidator, ScoreThresholdValidator, AssignmentValidator | 400 (validation), 403 (forbidden), 404 (not found), 409 (already qualified), 429 (rate limit) | QualificationResponse (score, tier, assigned_to) |
| GET /leads/{id} | LeadController | LeadService | LeadRepository | None (read-only) | lead:{id} (hash, cache-aside, TTL 5min) | leads, lead_interactions, lead_scores | None | Session token + PermissionValidator (owner, assigned rep, or admin) | 60 req/min per user | LeadExistsValidator | 403 (forbidden), 404 (not found), 429 (rate limit) | LeadResponse |
| GET /leads/search | LeadController | LeadService | LeadRepository | None (read-only) | lead:search:{query_hash} (sorted set, TTL 2min) | leads (full-text + optional vector search) | None | Session token + PermissionValidator (sales or admin) | 30 req/min per user | SearchQueryValidator, PaginationValidator, FilterValidator | 400 (invalid query), 429 (rate limit), 503 (vector search unavailable) | SearchLeadsResponse |
| POST /memory/update | MemoryController | MemoryService | MemoryRepository, ConversationRepository | MemoryUpdateRequested, MemoryFieldConfirmed, MemoryUpdated, MemoryEmbeddingUpdated | memory:{conv}:pending-confirm:{field} (TTL 15min, staged update) | memory_fields, memory_embeddings | update_memory_embedding (vector regeneration), reindex_memory (search index update) | Session token + ParticipantValidator | 30 req/min per user | MemoryFieldValidator, ConfirmationPolicyValidator, EmbeddingSizeValidator | 400 (validation), 404 (conversation not found), 422 (embedding too large), 429 (rate limit) | MemoryUpdateResponse (field, value, confirmation_required, embedding_status) |
| POST /memory/confirm | MemoryController | MemoryService | MemoryRepository, ConversationRepository | MemoryFieldConfirmed, MemoryUpdated | memory:{conv}:pending-confirm:{field} (del on confirm) | memory_fields (write on confirm), memory_embeddings | update_memory_embedding (vector regeneration after confirm) | Session token + ParticipantValidator | 20 req/min per user | ConfirmationTokenValidator, FieldExistsValidator, ExpiryValidator | 400 (validation), 404 (field not found), 410 (token expired), 429 (rate limit) | ConfirmationResponse (confirmed, updated_at) |
| GET /memory | MemoryController | MemoryService | MemoryRepository | None (read-only) | memory:{conv}:context (cached context string, TTL 1h) | memory_fields (for conversation) | None | Session token + ParticipantValidator | 60 req/min per user | ConversationExistsValidator | 404 (conversation not found), 429 (rate limit) | MemoryResponse (fields, values, last_updated) |
| GET /memory/search | MemoryController | MemoryService | MemoryRepository | None (read-only) | memory:{user}:semantic:{query_hash} (cache, TTL 5min) | memory_embeddings (vector similarity search) | None | Session token (any authenticated user) | 20 req/min per user | SearchQueryValidator, PaginationValidator | 400 (invalid query), 429 (rate limit), 503 (vector search unavailable) | SemanticMemoryResponse |
| POST /knowledge/search | KnowledgeController | KnowledgeDocumentService | KnowledgeDocumentRepository | None (read-only) | doc:search:cache:{query_hash} (cache, TTL 5min), doc:search:index (in-memory inverted index) | knowledge_documents (metadata filter), document_embeddings (vector search) | None | Session token (any authenticated user) | 30 req/min per user | SearchQueryValidator, PaginationValidator, FilterValidator | 400 (invalid query), 429 (rate limit), 503 (vector search unavailable) | SearchKnowledgeResponse |
| GET /knowledge/{id} | KnowledgeController | KnowledgeDocumentService | KnowledgeDocumentRepository | None (read-only) | doc:{id}:content (cache, TTL 1h) | knowledge_documents, document_versions | None | Session token + PermissionValidator (owner or shared access) | 60 req/min per user | DocumentExistsValidator | 403 (forbidden), 404 (not found), 429 (rate limit) | DocumentResponse |
| POST /workflows/execute | WorkflowController | WorkflowExecutionService | WorkflowExecutionRepository, WorkflowDefinitionRepository | WorkflowTriggered, WorkflowStepCompleted, WorkflowCompleted | wf:exec:{id}:state (hash, TTL 24h), wf:exec:{id}:lock (step transition lock), wf:queue:{worker_group} (list) | workflow_executions, execution_steps, execution_variables | execute_workflow_step (step runner), timeout_stuck_executions (maintenance) | Session token + PermissionValidator (workflow executor role) | 10 req/min per user, 50 req/min per tenant | WorkflowDefExistsValidator, InputSchemaValidator, TenantQuotaValidator, RateLimitValidator | 400 (validation), 403 (forbidden), 422 (quota exceeded), 429 (rate limit), 500 (execution error) | ExecutionResponse (execution_id, status, initial_step) |
| POST /workflows/{id}/compensate | WorkflowController | WorkflowExecutionService | WorkflowExecutionRepository | WorkflowCompensationStarted, WorkflowStepCompensated, WorkflowCompensationCompleted | wf:exec:{id}:state (update compensating state) | workflow_executions (compensation_status), execution_errors | compensate_workflow_step (compensation step runner) | Session token + PermissionValidator (admin only) | 5 req/min per user | ExecutionExistsValidator, CompensatableValidator, ExecutionStateValidator | 400 (validation), 403 (forbidden), 404 (not found), 409 (not compensatable), 429 (rate limit) | CompensationResponse (execution_id, compensation_status, steps_compensated) |
| GET /workflows/{id}/status | WorkflowController | WorkflowExecutionService | WorkflowExecutionRepository | None (read-only) | wf:exec:{id}:state (hash, TTL 30s) | workflow_executions, execution_steps | None | Session token + PermissionValidator (workflow owner or admin) | 60 req/min per user | ExecutionExistsValidator | 403 (forbidden), 404 (not found), 429 (rate limit) | WorkflowStatusResponse |
| GET /notifications | NotificationController | NotificationService | NotificationRepository | None (read-only) | notif:user:{id}:inbox (sorted set, last 200) | notifications | None | Session token (any authenticated user) | 30 req/min per user | PaginationValidator, FilterValidator | 400 (invalid pagination), 429 (rate limit) | NotificationListResponse |
| GET /notifications/pending | NotificationController | NotificationService | NotificationRepository | None (read-only) | notif:user:{id}:unread-count (integer, cached) | notifications WHERE status = pending AND user_id | None | Session token (any authenticated user) | 60 req/min per user | PaginationValidator | 429 (rate limit) | PendingNotificationsResponse |
| POST /notifications/test | NotificationController | NotificationService | NotificationRepository | NotificationTestSent | None (bypasses cache for test) | notifications (test log entry) | none (synchronous for test) | Session token + PermissionValidator (admin or developer) | 3 req/min per user | RecipientValidator, TemplateExistsValidator, TestModeValidator | 400 (validation), 403 (forbidden), 429 (rate limit) | TestNotificationResponse (delivered, preview_url) |
| GET /prompts/active | PromptController | PromptVersionService | PromptVersionRepository | None (read-only) | prompt:active:{prompt_id} (string, TTL infinite, invalidate on promote) | prompt_versions WHERE active = true | None | Session token + PermissionValidator (prompt reader role) | 120 req/min per user (high-volume) | PromptExistsValidator | 403 (forbidden), 404 (not found), 429 (rate limit) | ActivePromptResponse |
| GET /prompts/versions | PromptController | PromptVersionService | PromptVersionRepository | None (read-only) | prompt:versions:{prompt_id} (list, TTL 5min, invalidate on new version) | prompt_versions | None | Session token + PermissionValidator (prompt reader role) | 30 req/min per user | PromptExistsValidator, PaginationValidator | 403 (forbidden), 404 (not found), 429 (rate limit) | PromptVersionListResponse |
| POST /prompts/activate | PromptController | PromptVersionService | PromptVersionRepository | PromptVersionPromoted | prompt:active:{prompt_id} (set to new version hash, invalidate old) | prompt_versions (set active = false for old, active = true for new) | None (synchronous promote) | Session token + PermissionValidator (admin or prompt manager) | 5 req/min per user | VersionExistsValidator, AlreadyActiveValidator, RollbackPolicyValidator | 400 (validation), 403 (forbidden), 404 (version not found), 409 (already active), 429 (rate limit) | ActivateResponse (prompt_id, version, activated_at) |
| GET /analytics/conversations | AnalyticsController | AnalyticsService | None (read-model only) | None (read-only) | analytics:conversation:{scope} (hash, TTL 5min) | Aggregate queries on conversations + messages | None | Session token + PermissionValidator (analytics reader role) | 10 req/min per user | DateRangeValidator, ScopeValidator | 400 (invalid date range), 403 (forbidden), 429 (rate limit) | ConversationAnalyticsResponse |
| GET /analytics/meetings | AnalyticsController | AnalyticsService | None (read-model only) | None (read-only) | analytics:meeting:{scope} (hash, TTL 5min) | Aggregate queries on meetings + meeting_participants | None | Session token + PermissionValidator (analytics reader role) | 10 req/min per user | DateRangeValidator, ScopeValidator | 400 (invalid date range), 403 (forbidden), 429 (rate limit) | MeetingAnalyticsResponse |
| GET /analytics/leads | AnalyticsController | AnalyticsService | None (read-model only) | None (read-only) | analytics:lead:{scope} (hash, TTL 5min) | Aggregate queries on leads + lead_scores | None | Session token + PermissionValidator (analytics reader role) | 10 req/min per user | DateRangeValidator, ScopeValidator | 400 (invalid date range), 403 (forbidden), 429 (rate limit) | LeadAnalyticsResponse |
| GET /health | SystemController | HealthCheckService | None (connection pool check) | None | PING (Redis health check) | Connection pool check (DB health) | None | None (public endpoint) | 10 req/min per IP | None | 503 (unhealthy), 429 (rate limit) | SystemHealthResponse |
| GET /metrics | SystemController | MetricsService | None (in-memory + Redis counters) | None | metrics:{scope}:{period} (hash, TTL 30s) | Aggregated metrics queries | None | Internal network only (k8s liveness/readiness) | 5 req/min per IP | None | 503 (server error) | MetricsResponse |
| GET /config | SystemController | ConfigService | None (in-memory config) | None | config:runtime (hash, feature flags + settings) | None (config is env + Redis override) | None | Session token + PermissionValidator (admin only) | 5 req/min per user | None | 403 (forbidden), 429 (rate limit) | ConfigResponse |
| GET /system/status | SystemController | HealthCheckService | None (aggregate health) | None | PING + health keys (aggregate health) | Connection pool + read-replica lag | None | Session token + PermissionValidator (admin only) | 5 req/min per user | None | 403 (forbidden), 503 (degraded), 429 (rate limit) | SystemStatusResponse |
# 8. Background Job Mapping

This section defines the complete Celery worker topology for the system. Eight dedicated worker pools own specific task families. Workers communicate exclusively through Redis (broker + result backend) and access shared infrastructure via dependency-injected adapters. Each worker is independently deployable and horizontally scalable.

---

## 8.1 Worker Configuration Table

### meeting_worker

Purpose: Meeting scheduling, cancellation, confirmation, availability checks, n8n webhook calls

| Parameter | Value |
|---|---|
| Queue Name | queue:meeting |
| Priority (1-10) | 8 |
| Retry Policy | exponential_backoff (2s, 4s, 8s, 16s, 32s) |
| Max Retries | 5 |
| Soft Timeout | 120s |
| Hard Timeout | 300s |
| Concurrency | 4 (scale to 8 under load) |
| Dependencies | n8n webhook client, MeetingRepository, UserProfileRepository, CalendarProviderAdapter, ConferenceLinkProvisioner |
| Tasks Owned | schedule_meeting, cancel_meeting, confirm_meeting, reschedule_meeting, check_availability, send_meeting_notifications, trigger_n8n_meeting_webhook, sync_calendar_event, provision_conference_link |

### notification_worker

Purpose: Email, push, SMS delivery, retry logic, dead letter queue processing

| Parameter | Value |
|---|---|
| Queue Name | queue:notification |
| Priority (1-10) | 7 |
| Retry Policy | exponential_backoff (1s, 3s, 9s, 27s, 81s) |
| Max Retries | 5 |
| Soft Timeout | 60s |
| Hard Timeout | 120s |
| Concurrency | 8 (IO-bound, max 16) |
| Dependencies | EmailProviderAdapter (SES/SendGrid), PushProviderAdapter (FCM/APNs), SMSProviderAdapter (Twilio), NotificationRepository, TemplateRenderer, DeliveryTracker |
| Tasks Owned | send_email_notification, send_push_notification, send_sms_notification, deliver_in_app_notification, deliver_slack_notification, retry_failed_delivery, process_notification_dead_letter, failover_alternate_channel |

### memory_worker

Purpose: Memory field confirmation, memory updates, memory confidence recalculation

| Parameter | Value |
|---|---|
| Queue Name | queue:memory |
| Priority (1-10) | 6 |
| Retry Policy | fixed_rate (5s interval) |
| Max Retries | 3 |
| Soft Timeout | 30s |
| Hard Timeout | 60s |
| Concurrency | 6 |
| Dependencies | MemoryRepository, ConversationRepository, MemoryFieldRegistry, ConfirmationTokenStore (Redis) |
| Tasks Owned | confirm_memory_field, update_memory_field_value, recalculate_memory_confidence, expire_staged_memory_updates, sync_memory_to_long_term, verify_memory_consistency |

### embedding_worker

Purpose: Embedding generation, vector index updates, re-indexing

| Parameter | Value |
|---|---|
| Queue Name | queue:embedding |
| Priority (1-10) | 5 |
| Retry Policy | exponential_backoff (2s, 8s, 32s) |
| Max Retries | 3 |
| Soft Timeout | 120s |
| Hard Timeout | 300s |
| Concurrency | 2 (CPU/memory-bound, GPU-optional) |
| Dependencies | EmbeddingModelAPI (OpenAI/text-embedding-3-large or local), VectorStoreAdapter (Pinecone/Qdrant), KnowledgeDocumentRepository, MemoryRepository |
| Tasks Owned | generate_document_embedding, generate_memory_embedding, update_vector_index, reindex_all_documents, rebuild_search_index, refresh_stale_embeddings, remove_orphan_embeddings |

### summary_worker

Purpose: Conversation summary generation, long-term memory archiving

| Parameter | Value |
|---|---|
| Queue Name | queue:summary |
| Priority (1-10) | 4 |
| Retry Policy | exponential_backoff (5s, 25s, 125s) |
| Max Retries | 3 |
| Soft Timeout | 180s |
| Hard Timeout | 600s |
| Concurrency | 3 |
| Dependencies | LLM gateway (OpenAI/Anthropic), ConversationRepository, KnowledgeDocumentRepository, PromptVersionRepository, MemoryRepository |
| Tasks Owned | generate_conversation_summary, generate_meeting_summary, archive_long_term_memory, store_summary_to_knowledge_base, backtest_prompt_version, evaluate_prompt_version |

### analytics_worker

Purpose: Conversation analytics, meeting analytics, lead analytics, aggregation jobs

| Parameter | Value |
|---|---|
| Queue Name | queue:analytics |
| Priority (1-10) | 3 |
| Retry Policy | fixed_rate (60s interval) |
| Max Retries | 2 |
| Soft Timeout | 300s |
| Hard Timeout | 600s |
| Concurrency | 2 |
| Dependencies | ClickHouseClient (analytics DB), MetricsAggregator, PrometheusPushGateway, MaterializedViewBuilder, DataLakeClient |
| Tasks Owned | aggregate_conversation_analytics, aggregate_meeting_analytics, aggregate_lead_analytics, run_daily_rollup, run_weekly_rollup, build_dashboard_cache, compute_sla_metrics, export_analytics_to_crm, calculate_conversion_funnels |

### workflow_worker

Purpose: Saga orchestration, compensation triggers, workflow step execution

| Parameter | Value |
|---|---|
| Queue Name | queue:workflow |
| Priority (1-10) | 9 (highest business priority) |
| Retry Policy | exponential_backoff (2s, 8s, 32s) |
| Max Retries | 3 |
| Soft Timeout | 60s |
| Hard Timeout | 120s |
| Concurrency | 5 |
| Dependencies | WorkflowExecutionRepository, SagaStateStore (Redis), CompensationHandlerRegistry, n8n webhook client, StepDefinitionRegistry |
| Tasks Owned | execute_workflow_step, compensate_workflow_step, orchestrate_saga, trigger_compensation, timeout_stuck_executions, replay_dead_letter_step, notify_saga_failure, rollback_aggregate_state |

### cleanup_worker

Purpose: Idle conversation timeout, expired lock cleanup, data retention, stale prompt cleanup

| Parameter | Value |
|---|---|
| Queue Name | queue:cleanup |
| Priority (1-10) | 1 (lowest — maintenance only) |
| Retry Policy | fixed_rate (300s interval) |
| Max Retries | 2 |
| Soft Timeout | 300s |
| Hard Timeout | 600s |
| Concurrency | 1 (singleton — prevent conflicting cleanups) |
| Dependencies | All repository interfaces (read-only for scans, write for deletions), Redis (SCAN + DEL), S3/BlobStorageClient, DataRetentionPolicyRegistry, StaleEntityDetector |
| Tasks Owned | timeout_idle_conversations, cleanup_expired_locks, enforce_data_retention_policies, purge_stale_prompt_versions, archive_old_workflow_executions, cleanup_orphan_recordings, remove_orphan_embeddings, vacuum_dead_letter_queues, expire_staged_memory_updates, rotate_analytics_partitions |

---

## 8.2 Infrastructure Connectivity Diagram

    ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
    │  Celery Worker Topology — Infrastructure Connectivity                                               │
    │                                                                                                     │
    │  Legend: ──► synchronous data flow    - - ► async queue flow    ~~► event-driven                    │
    │                                                                                                     │
    │                                  ┌─────────────────────────────────────────────────────┐           │
    │                                  │              Redis (Broker + Backend)               │           │
    │                                  │  lists: queue:meeting, queue:notification, ...       │           │
    │                                  │  pub/sub: worker:{name}:heartbeat, saga:{id}:state   │           │
    │                                  │  result: celery-task-meta-{task_id} (TTL 24h)        │           │
    │                                  └──────┬────────────────────┬──────────────────────────┘           │
    │                                          │                    │                                     │
    │              ┌───────────────────────────┼────────────────────┼───────────────────────────────┐     │
    │              │          ┌────────────────┘                    └────────────────┐              │     │
    │              │          ▼                                                      ▼              │     │
    │              │  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐ │     │
    │              │  │ meeting_wrk   │   │notification   │   │ memory_wrk    │   │ embedding_wrk │ │     │
    │              │  │ concurrency:4 │   │_wrk conc:8    │   │ concurrency:6 │   │ concurrency:2 │ │     │
    │              │  └───┬───────┬───┘   └───┬───────┬───┘   └───┬───────┬───┘   └───┬───────┬───┘ │     │
    │              │      │       │           │       │           │       │           │       │     │     │
    │              │      ▼       ▼           ▼       ▼           ▼       ▼           ▼       ▼     │     │
    │              │  ┌──────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌──────┐│     │
    │              │  │Post- │ │ n8n  │ │ Email  │ │ Push/  │ │Post- │ │Confrm  │ │Vector  │ │Embed ││     │
    │              │  │gres  │ │Webhok│ │Provider│ │ SMS    │ │gres  │ │Token   │ │Store   │ │Model ││     │
    │              │  └──────┘ └──────┘ └────────┘ └────────┘ └──────┘ │(Redis) │ │(Pine/  │ │API   ││     │
    │              │                                                  └────────┘ │ Qdrant)│ └──────┘│     │
    │              │                                                           └────────┘         │     │
    │              │                                                                               │     │
    │              │  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐   ┌───────────────┐ │     │
    │              │  │ summary_wrk   │   │ analytics_wrk │   │ workflow_wrk  │   │ cleanup_wrk   │ │     │
    │              │  │ concurrency:3 │   │ concurrency:2 │   │ concurrency:5 │   │ concurrency:1 │ │     │
    │              │  └───┬───────┬───┘   └───┬───────┬───┘   └───┬───────┬───┘   └───┬───────┬───┘ │     │
    │              │      │       │           │       │           │       │           │       │     │     │
    │              │      ▼       ▼           ▼       ▼           ▼       ▼           ▼       ▼     │     │
    │              │  ┌──────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌──────┐│     │
    │              │  │LLM   │ │Post- │ │Click-  │ │Prom-   │ │Post- │ │ Saga   │ │ n8n   │ │Post-  ││     │
    │              │  │Gate- │ │gres  │ │House   │ │etheus  │ │gres  │ │ Store  │ │Webhok │ │gres   ││     │
    │              │  │way   │ │(Conv)│ │(Anlytc)│ │PushGW  │ │(Wkfl) │ │(Redis) │ │       │ │(All)  ││     │
    │              │  └──────┘ └──────┘ └────────┘ └────────┘ └──────┘ └────────┘ └────────┘ └──────┘│     │
    │              │                                                                                   │     │
    │              │  All workers share:                                                               │     │
    │              │    Redis: broker (list pop), result backend (task status writes),                 │     │
    │              │           rate-limit keys, distributed locks, saga state                          │     │
    │              │    PostgreSQL: via repository interfaces (read/write per owned task set)          │     │
    │              │    LLM Gateway: summary_worker, memory_worker, embedding_worker                   │     │
    │              │    n8n: meeting_worker, workflow_worker (webhook POST), cleanup_worker (status)   │     │
    │              └───────────────────────────────────────────────────────────────────────────────┘     │
    └─────────────────────────────────────────────────────────────────────────────────────────────────────┘

---

## 8.3 Worker Routing Table

Each task is routed to its owned worker via a dedicated Celery queue. The routing key follows a dot-delimited hierarchy for future sub-queue expansion.

| Task Name Pattern | Routed To | Queue Name | Routing Key |
|---|---|---|---|
| schedule_meeting, cancel_meeting, confirm_meeting, reschedule_meeting, check_availability, send_meeting_notifications, trigger_n8n_meeting_webhook, sync_calendar_event, provision_conference_link | meeting_worker | queue:meeting | meeting.# |
| send_email_notification, send_push_notification, send_sms_notification, deliver_in_app_notification, deliver_slack_notification, retry_failed_delivery, process_notification_dead_letter, failover_alternate_channel | notification_worker | queue:notification | notification.# |
| confirm_memory_field, update_memory_field_value, recalculate_memory_confidence, expire_staged_memory_updates, sync_memory_to_long_term, verify_memory_consistency | memory_worker | queue:memory | memory.# |
| generate_document_embedding, generate_memory_embedding, update_vector_index, reindex_all_documents, rebuild_search_index, refresh_stale_embeddings, remove_orphan_embeddings | embedding_worker | queue:embedding | embedding.# |
| generate_conversation_summary, generate_meeting_summary, archive_long_term_memory, store_summary_to_knowledge_base, backtest_prompt_version, evaluate_prompt_version | summary_worker | queue:summary | summary.# |
| aggregate_conversation_analytics, aggregate_meeting_analytics, aggregate_lead_analytics, run_daily_rollup, run_weekly_rollup, build_dashboard_cache, compute_sla_metrics, export_analytics_to_crm, calculate_conversion_funnels | analytics_worker | queue:analytics | analytics.# |
| execute_workflow_step, compensate_workflow_step, orchestrate_saga, trigger_compensation, timeout_stuck_executions, replay_dead_letter_step, notify_saga_failure, rollback_aggregate_state | workflow_worker | queue:workflow | workflow.# |
| timeout_idle_conversations, cleanup_expired_locks, enforce_data_retention_policies, purge_stale_prompt_versions, archive_old_workflow_executions, cleanup_orphan_recordings, remove_orphan_embeddings, vacuum_dead_letter_queues, expire_staged_memory_updates, rotate_analytics_partitions | cleanup_worker | queue:cleanup | cleanup.# |

Celery configuration for routing:

    CELERY_TASK_ROUTES = {
        "meeting.*":         {"queue": "queue:meeting"},
        "notification.*":    {"queue": "queue:notification"},
        "memory.*":          {"queue": "queue:memory"},
        "embedding.*":       {"queue": "queue:embedding"},
        "summary.*":         {"queue": "queue:summary"},
        "analytics.*":       {"queue": "queue:analytics"},
        "workflow.*":        {"queue": "queue:workflow"},
        "cleanup.*":         {"queue": "queue:cleanup"},
    }
    
    CELERY_TASK_DEFAULT_QUEUE = "queue:default"
    CELERY_TASK_DEFAULT_EXCHANGE = "tasks"
    CELERY_TASK_DEFAULT_EXCHANGE_TYPE = "topic"
    CELERY_TASK_DEFAULT_ROUTING_KEY = "default.#"

---

## 8.4 Rate Limiting Per Worker Queue

Each queue enforces a task execution rate limit at the worker level. Tasks that exceed the rate are re-queued (not dropped) unless otherwise specified.

| Worker Queue | Default Rate (tasks/min) | Burst Limit | Window Type | Exceeded Action | Rationale |
|---|---|---|---|---|---|
| queue:meeting | 60 | 120 | 1 min sliding | Re-queue (back-pressure) | Meeting operations call external calendar APIs with strict rate limits |
| queue:notification | 200 | 400 | 1 min sliding | Re-queue (back-pressure) | Email/push providers throttle at provider level; internal queue absorbs spikes |
| queue:memory | 100 | 200 | 1 min sliding | Re-queue (back-pressure) | Memory operations are lightweight DB writes; burst absorption is safe |
| queue:embedding | 20 | 40 | 1 min sliding | Reject (return to source queue) | Embedding model API has hard concurrency limits; rejection prevents cascading failure |
| queue:summary | 10 | 20 | 1 min sliding | Reject (return to source queue) | LLM gateway has token-based throttling; rejection prevents context window overflow |
| queue:analytics | 5 | 10 | 5 min sliding | Skip if same-type task pending | Analytics aggregation is idempotent; duplicate skips are safe |
| queue:workflow | 40 | 80 | 1 min sliding | Re-queue (back-pressure) | Saga steps have strict ordering; back-pressure prevents step overlap |
| queue:cleanup | 2 | 4 | 10 min sliding | Skip if previous run in progress | Cleanup tasks are singleton operations; overlapping runs are destructive |

Rate limit key pattern in Redis:

    rate-limit:worker:{worker_name}:{task_name}:{period_start}
    
    Structure: Hash with fields "count" (integer) and "window_start" (timestamp).
    
    Example: rate-limit:worker:embedding:generate_document_embedding:1689379200
             { "count": 15, "window_start": 1689379200 }

---

## 8.5 Graceful Shutdown Strategy

All workers implement a four-phase graceful shutdown protocol. This ensures in-flight tasks are not lost and side effects (webhook calls, database writes) complete before process termination.

    Phase 1 — SIGTERM Received (t+0s)
    
        ┌─────────────────────────────────────────────────────────────────────┐
        │ 1. Worker sets internal state to SHUTTING_DOWN.                     │
        │ 2. Worker stops consuming new messages from broker queues            │
        │    (basic_cancel on all consumer tags).                              │
        │ 3. Worker broadcasts shutdown notification to Redis pub/sub:         │
        │    channel: worker:{name}:events                                     │
        │    payload: { "event": "shutdown_started", "worker": "{name}",      │
        │               "hostname": "{host}", "pool_size": {n} }              │
        │ 4. Health check endpoint /health/readiness returns 503.              │
        │ 5. Prometheus gauge celery_workers_active{worker="{name}"} set to 0. │
        └─────────────────────────────────────────────────────────────────────┘
    
    Phase 2 — In-Flight Task Drain (t+0s to t+warm_timeout)
    
        ┌─────────────────────────────────────────────────────────────────────┐
        │ warm_timeout = max(soft_timeout + 30s, 60s) for the worker pool.    │
        │                                                                     │
        │ For each worker type:                                               │
        │   meeting_worker:     warm_timeout = 150s (120s soft + 30s)         │
        │   notification_worker: warm_timeout = 90s  (60s soft + 30s)         │
        │   memory_worker:      warm_timeout = 60s  (30s soft + 30s)          │
        │   embedding_worker:   warm_timeout = 150s (120s soft + 30s)         │
        │   summary_worker:     warm_timeout = 210s (180s soft + 30s)         │
        │   analytics_worker:   warm_timeout = 330s (300s soft + 30s)         │
        │   workflow_worker:    warm_timeout = 90s  (60s soft + 30s)          │
        │   cleanup_worker:     warm_timeout = 330s (300s soft + 30s)         │
        │                                                                     │
        │ During drain:                                                       │
        │   1. Currently executing tasks continue normally.                    │
        │   2. No new tasks are accepted from the broker.                     │
        │   3. If a task exceeds warm_timeout, it is revoked:                 │
        │      a. Task receives a SIGUSR1 (Celery revoke signal).             │
        │      b. Task result set to REVOKED in result backend.               │
        │      c. Revoked task is re-queued to the source queue with          │
        │         delivery_mode=2 (persistent) and a revoke_count header.     │
        │   4. Completed task results are flushed to the result backend.      │
        └─────────────────────────────────────────────────────────────────────┘
    
    Phase 3 — Connection Pool Drain (t+warm_timeout to t+warm_timeout + 15s)
    
        ┌─────────────────────────────────────────────────────────────────────┐
        │ 1. Database connection pool: pool.close() with timeout=10s.         │
        │    Any connections still in use are forcibly closed.                │
        │ 2. Redis connection pool: connection_pool.disconnect().             │
        │    In-flight Redis commands are waited on up to 5s.                 │
        │ 3. HTTP sessions (LLM gateway, n8n):                              │
        │    aiohttp.ClientSession.close() with timeout=5s.                   │
        │    Outstanding requests are cancelled and logged.                   │
        │ 4. Open file handles (log files, temp files) are flushed and closed.│
        └─────────────────────────────────────────────────────────────────────┘
    
    Phase 4 — Process Exit (t+warm_timeout + 15s)
    
        ┌─────────────────────────────────────────────────────────────────────┐
        │ 1. Worker logs final shutdown summary:                              │
        │    {                                                                │
        │      "event": "shutdown_complete",                                  │
        │      "worker": "{name}",                                            │
        │      "tasks_completed": {n},                                        │
        │      "tasks_revoked": {m},                                          │
        │      "drain_duration_seconds": {d},                                 │
        │      "exit_code": {code}                                            │
        │    }                                                                │
        │ 2. If tasks_revoked > 0:                                            │
        │      Exit code = 1 (signal orchestrator that work was lost)         │
        │    Else:                                                            │
        │      Exit code = 0 (clean shutdown)                                 │
        │ 3. Orchestrator (Kubernetes / supervisord):                         │
        │    - On exit code 0: immediate restart allowed.                     │
        │    - On exit code 1: delay restart by 30s to allow                  │
        │      revoked task re-queue propagation across broker.               │
        │ 4. Prometheus metric celery_worker_shutdown_duration_seconds         │
        │    records the total shutdown time for monitoring.                  │
        └─────────────────────────────────────────────────────────────────────┘
    
    Worker shutdown timeout configuration (per worker type):
    
        CELERY_WORKER_SHUTDOWNTIME = {
            "meeting_worker":     150,   # seconds
            "notification_worker": 90,
            "memory_worker":       60,
            "embedding_worker":   150,
            "summary_worker":     210,
            "analytics_worker":   330,
            "workflow_worker":     90,
            "cleanup_worker":     330,
        }
    
    Celery worker command-line flags for graceful shutdown:
    
        celery --app=app.tasks worker \
            --queues=queue:{name} \
            --concurrency={n} \
            --loglevel=INFO \
            --without-gossip \
            --without-mingle \
            --without-heartbeat \
            --time-limit={hard_timeout} \
            --soft-time-limit={soft_timeout} \
            --max-tasks-per-child=1000 \
            --prefetch-multiplier=1


# 9. Redis Blueprint

This section defines every Redis key in the system with its full specification,
including TTL, purpose, eviction strategy, data type, ownership, and failover
behavior. The Redis instance is a production-grade cluster with replication and
persistence (RDB + AOF). All keys follow a colon-delimited namespace convention
for logical grouping and Redis cluster hash-slot distribution.

## 9.1 Redis Key Hierarchy

    redis
    |
    ├── conversation:* ...................... Conversation state and messaging
    │   ├── conversation:{id} .............. Full conversation state (hash)
    │   ├── conversation:{id}:messages ..... Recent messages ring buffer (list)
    │   ├── conversation:{id}:lock ......... Pessimistic write lock (string)
    │   └── conversation:{id}:context ...... Compressed LLM context (string)
    |
    ├── session:* ........................... Identity and session management
    │   ├── session:{id} .................. Anonymous session data (hash)
    │   └── identity:{user_id} ............. Resolved identity cache (hash)
    |
    ├── memory:* ............................ Long-term memory subsystem
    │   ├── memory:{user_id} .............. Recent memory entries (sorted set)
    │   └── memory:{user_id}:confirmations  Pending confirmation queue (list)
    |
    ├── meeting:* ........................... Meeting scheduling and calendar
    │   ├── meeting-lock:{id} ............. Scheduling lock (string)
    │   ├── meeting:availability:{date} ... Cached availability slots (bitmap)
    │   └── meeting:calendar:{user} ....... Cached calendar data (sorted set)
    |
    ├── idempotency:* ...................... Idempotency and deduplication
    │   └── idempotency:{key} ............. Idempotency lock (string)
    |
    ├── rate-limit:* ....................... Rate limiting counters
    │   ├── rate-limit:{user}:{endpoint} .. Per-user sliding window (sorted set)
    │   └── rate-limit:{ip}:{endpoint} .... Per-IP rate counter (sorted set)
    |
    ├── cache:* ............................ General-purpose caches
    │   ├── tool-cache:{hash} ............. Tool execution result cache (string)
    │   ├── knowledge:search:{hash} ....... Knowledge search result cache (string)
    │   ├── prompt:active:{context} ....... Active prompt version cache (string)
    │   └── summary:{conversation_id} ..... Conversation summary cache (string)
    |
    ├── lock:* ............................. Distributed lock primitives
    │   ├── lock:{resource} ............... Generic distributed lock (string)
    │   └── saga:{id}:lock ................ Saga execution lock (string)
    |
    └── celery:* ........................... Worker management and monitoring
        └── celery:worker:{name}:status ... Worker heartbeat and status (hash)

## 9.2 Conversation Keys

### conversation:{id}

| Field | Value |
|---|---|
| TTL | 1 hour (extended on every read/write) |
| Purpose | Stores full conversation state: participant list, status, created_at, last_activity, metadata. Acts as the hot cache for the Conversation aggregate to avoid DB reads on every message. |
| Eviction Strategy | allkeys-lru (if maxmemory reached); otherwise passive expiry on TTL |
| Data Type | Hash -- fields: status, participant_ids, created_at, last_activity_at, message_count, metadata_json |
| Ownership | Conversation aggregate (domain layer writes, read by application layer) |
| Failover Behavior | On cache miss, load from PostgreSQL conversation tables. TTL refresh on every read ensures active conversations remain cached. |

### conversation:{id}:messages

| Field | Value |
|---|---|
| TTL | 1 hour (extended on every append) |
| Purpose | Ring buffer of the last N messages (N=50) for fast conversation hydration on reconnect and LLM context assembly. Eliminates DB round-trip for recent message history. |
| Eviction Strategy | allkeys-lru; list is explicitly trimmed to N via LTRIM on every LPUSH |
| Data Type | List -- each element is a JSON-serialized message object: {id, role, content, timestamp, metadata} |
| Ownership | Conversation aggregate (appended by MessageProcessingService, read by GetConversationHandler) |
| Failover Behavior | On cache miss, fall back to conversation_messages table with LIMIT 50 ORDER BY created_at DESC. Cache is re-primed on read. |

### conversation:{id}:lock

| Field | Value |
|---|---|
| TTL | 30 seconds (auto-release via TTL if holder crashes) |
| Purpose | Pessimistic distributed lock for write operations (append message, update state). Prevents concurrent writes to the same conversation from different application instances. |
| Eviction Strategy | No eviction -- TTL-based auto-release. Key is deleted on explicit unlock. |
| Data Type | String -- holds the lock owner identifier (instance_id:request_id) |
| Ownership | MessageProcessingService (application layer) |
| Failover Behavior | On lock acquisition failure (key exists), retry with backoff up to 3 times (100ms, 200ms, 400ms). If still locked, return 429 Too Many Requests. On Redis node failure, lock is automatically released when TTL expires. |

### conversation:{id}:context

| Field | Value |
|---|---|
| TTL | 5 minutes (expires after conversation inactivity) |
| Purpose | Compressed conversation context for LLM calls. Stores the condensed representation (summary + key facts + recent messages) to avoid reconstructing from raw messages on every LLM call. |
| Eviction Strategy | volatile-lru -- context is recomputable from source data |
| Data Type | String -- JSON-serialized context object: {summary, key_facts[], last_n_messages[], token_count} |
| Ownership | ResponseGenerationService (application layer, written by ContextBuilder) |
| Failover Behavior | On cache miss, ContextBuilder rebuilds from conversation:{id}:messages + conversation:{id} hash. If source messages are also missing, fall back to PostgreSQL. |

## 9.3 Identity Keys

### session:{id}

| Field | Value |
|---|---|
| TTL | 24 hours (extended on each authenticated request) |
| Purpose | Stores session data for anonymous and authenticated users. Contains user_id, roles, permissions, tenant_id, and session metadata. Avoids session DB lookup on every request. |
| Eviction Strategy | volatile-ttl -- sessions expire naturally based on activity |
| Data Type | Hash -- fields: user_id, roles[], tenant_id, created_at, last_activity_at, ip_address, user_agent |
| Ownership | IdentityMiddleware (middleware layer, written by auth service) |
| Failover Behavior | On cache miss, load from user_auth_tokens table. If also missing from DB, treat as unauthenticated. On Redis node failure, all sessions are evaluated from the DB (degraded auth). |

### identity:{user_id}

| Field | Value |
|---|---|
| TTL | 10 minutes (invalidated on profile/role change) |
| Purpose | Resolved identity cache that stores the complete user profile snapshot: display_name, email, roles, permissions, preferences, and tenant mapping. Prevents profile DB lookup on every internal service call. |
| Eviction Strategy | volatile-lru -- identity is recomputable from user_profiles table |
| Data Type | Hash -- fields: user_id, display_name, email, roles[], permissions[], preferences_json, tenant_id, avatar_url |
| Ownership | UserProfile aggregate (written by UserProfileService, read by all internal services) |
| Failover Behavior | On cache miss, load from user_profiles table with role and permission joins. On Redis node failure, every internal call hits the DB directly. Explicit invalidation on UserProfileUpdated event. |

## 9.4 Memory Keys

### memory:{user_id}

| Field | Value |
|---|---|
| TTL | 2 hours (extended on each memory operation) |
| Purpose | Stores recent memory entries for a user in chronological order. Each entry is a key-value pair representing a learned fact about the user (name, preferences, context). Used by the LLM to personalize responses. |
| Eviction Strategy | volatile-lru -- memory is backed by PostgreSQL long-term store |
| Data Type | Sorted Set -- score = Unix timestamp of memory creation, member = JSON object {field, value, confidence, source, created_at} |
| Ownership | MemoryService (application layer, read by ResponseGenerationService) |
| Failover Behavior | On cache miss, load from conversation_memory table with LIMIT 50. On Redis node failure, memory is read from PostgreSQL for every request (degraded latency). |

### memory:{user_id}:confirmations

| Field | Value |
|---|---|
| TTL | 15 minutes (confirmation window) |
| Purpose | Pending confirmation queue for memory fields that require explicit user consent before being committed to long-term storage. Stores staged updates awaiting ConfirmMemoryField command. |
| Eviction Strategy | volatile-ttl -- expired confirmations are garbage-collected by TTL |
| Data Type | List -- each element is a JSON object {confirmation_token, field, value, context, created_at} |
| Ownership | MemoryService (written by UpdateMemoryHandler, read by ConfirmMemoryFieldHandler) |
| Failover Behavior | On cache miss, the confirmation token is considered expired. The user is prompted to re-submit the memory update. On Redis node failure, pending confirmations are lost (acceptable -- user is asked to confirm again). |

## 9.5 Meeting Keys

### meeting-lock:{id}

| Field | Value |
|---|---|
| TTL | 10 seconds (auto-release -- scheduling is fast) |
| Purpose | Distributed lock for meeting scheduling operations. Prevents double-booking of the same time slot by concurrent requests from different application instances or users. |
| Eviction Strategy | No eviction -- TTL-based auto-release. Deleted on explicit unlock after scheduling completes. |
| Data Type | String -- holds lock owner identifier |
| Ownership | MeetingService (application layer, acquired by ScheduleMeetingHandler) |
| Failover Behavior | On lock acquisition failure, return 409 Conflict with retry-after header. On Redis node failure, scheduling degrades to optimistic concurrency with database-level unique constraint on (start_time, participant_id). |

### meeting:availability:{date}

| Field | Value |
|---|---|
| TTL | 30 seconds (availability changes in real-time) |
| Purpose | Cached availability bitmap for a given date. 96 bits represent 15-minute slots from 00:00 to 23:45. Set bit = available, cleared bit = booked or locked. Avoids recomputing availability on every calendar view. |
| Eviction Strategy | volatile-ttl -- short TTL ensures freshness |
| Data Type | Bitmap (96 bits stored as 12-byte binary string) |
| Ownership | MeetingService (written by GetMeetingAvailabilityHandler, read by ScheduleMeetingHandler and calendar UI) |
| Failover Behavior | On cache miss, rebuild bitmap from meetings table + Redis slot locks. On Redis node failure, compute availability directly from PostgreSQL for every request (acceptable for scheduling UI, latency increases to ~200ms). |

### meeting:calendar:{user}

| Field | Value |
|---|---|
| TTL | 2 minutes (calendar changes are infrequent) |
| Purpose | Cached calendar data for a user for the current week/month view. Stores meeting IDs and time ranges to avoid repeated DB queries on calendar navigation. |
| Eviction Strategy | volatile-lru -- calendar is recomputable |
| Data Type | Sorted Set -- score = Unix timestamp of meeting start, member = meeting_id |
| Ownership | MeetingService (written by calendar sync, read by GetUserMeetingsHandler) |
| Failover Behavior | On cache miss, query meetings JOIN meeting_participants with date range filter. On Redis node failure, every calendar load hits PostgreSQL (latency increase ~50ms). |

## 9.6 Idempotency Keys

### idempotency:{key}

| Field | Value |
|---|---|
| TTL | 24 hours (idempotency window) |
| Purpose | Idempotency lock that ensures a request with a given idempotency key is processed exactly once. The key is derived from the client-supplied Idempotency-Key header. If the key exists, the stored response is returned without re-execution. |
| Eviction Strategy | volatile-ttl -- keys expire after the idempotency window |
| Data Type | String -- JSON-serialized response object: {status_code, body, headers, created_at} |
| Ownership | API Gateway / IdempotencyMiddleware (middleware layer) |
| Failover Behavior | On cache miss (key expired or not set), execute the request normally. On Redis node failure, idempotency guarantee is lost for that window -- the client must retry with a new key. Critical writes use database-level unique constraints as a secondary guard. |

## 9.7 Rate Limiting Keys

### rate-limit:{user}:{endpoint}

| Field | Value |
|---|---|
| TTL | Varies by rate limit window (typically 1 second, 1 minute, or 1 hour) |
| Purpose | Sliding window rate counter for authenticated users. Tracks request timestamps to enforce per-user rate limits per endpoint. Uses a sorted set for precise sliding window counting. |
| Eviction Strategy | volatile-ttl -- keys expire naturally at window end |
| Data Type | Sorted Set -- score = Unix timestamp of request, member = unique request ID. Count is derived from ZCOUNT in the window range. |
| Ownership | RateLimitMiddleware (middleware layer) |
| Failover Behavior | On Redis node failure, rate limiting is bypassed (degraded mode). A circuit breaker opens if Redis is unreachable for > 5 seconds. In-memory approximate counters provide best-effort rate limiting during failover. |

### rate-limit:{ip}:{endpoint}

| Field | Value |
|---|---|
| TTL | Varies by rate limit window (typically 1 second, 1 minute, or 1 hour) |
| Purpose | Per-IP sliding window rate counter for unauthenticated requests. Prevents IP-based abuse and DDoS attacks. Same mechanism as user rate limiting but keyed by IP address instead of user ID. |
| Eviction Strategy | volatile-ttl -- keys expire naturally at window end |
| Data Type | Sorted Set -- score = Unix timestamp, member = request ID |
| Ownership | RateLimitMiddleware (middleware layer) |
| Failover Behavior | Same as rate-limit:{user}:{endpoint}. On Redis failure, IP rate limiting is degraded to approximate in-memory counters with relaxed limits to avoid false positives during failover. |

## 9.8 Cache Keys

### tool-cache:{hash}

| Field | Value |
|---|---|
| TTL | 30 minutes (configurable per tool, default 30 min) |
| Purpose | Caches the result of deterministic tool executions (e.g., calculator, weather lookup, data retrieval). The hash is derived from tool_name + SHA256(arguments). Idempotent tools with identical inputs return cached results. |
| Eviction Strategy | allkeys-lru -- cache is purely an optimization |
| Data Type | String -- JSON-serialized tool result: {result, execution_time_ms, cached_at, tool_version} |
| Ownership | ToolExecutionService (tools layer) |
| Failover Behavior | On cache miss, execute the tool normally. On Redis node failure, caching is disabled; every tool call executes. Tools marked as non-cacheable (write operations, random generators) skip the cache entirely. |

### knowledge:search:{hash}

| Field | Value |
|---|---|
| TTL | 5 minutes (default), 30 seconds (filtered searches) |
| Purpose | Caches knowledge search results (top-10 document IDs + relevance scores) to avoid expensive vector search and cross-encoder re-ranking for identical queries. Hash is SHA256(normalized_query + tenant_id + filters). |
| Eviction Strategy | allkeys-lru -- cache is recomputable from vector store |
| Data Type | String -- JSON-serialized search result: {results: [{document_id, score, title, snippet}], total_hits, query_time_ms} |
| Ownership | SearchKnowledgeHandler / RAG pipeline (application / AI/ML layer) |
| Failover Behavior | On cache miss, execute vector search + re-ranking pipeline. On Redis node failure, every search query goes through the full pipeline (latency increases ~500ms). |

### prompt:active:{context}

| Field | Value |
|---|---|
| TTL | 1 hour (invalidated on prompt promotion/rollback) |
| Purpose | Caches the active (production) prompt version content for a given context (prompt_id + optional environment tag). Eliminates version lookup on every LLM call. The version hash or content is stored. |
| Eviction Strategy | volatile-lru -- active prompt is versioned and promotable |
| Data Type | String -- JSON object: {prompt_id, version, content, model_config, created_at, promoted_at} |
| Ownership | PromptVersion aggregate (written by PromptVersionService, read by ResponseGenerationService) |
| Failover Behavior | On cache miss, fetch from prompt_versions WHERE active=true. On Redis node failure, every LLM call fetches from PostgreSQL. Explicit invalidation on PromptVersionPromoted and PromptVersionRolledBack events. |

### summary:{conversation_id}

| Field | Value |
|---|---|
| TTL | 1 hour (regenerated on new messages) |
| Purpose | Cached conversation summary generated by the LLM. Stores the condensed summary text, key points, and token count. Avoids re-summarization on every summary request. |
| Eviction Strategy | volatile-lru -- summary is recomputable from messages |
| Data Type | String -- JSON object: {summary_text, key_points[], token_count, generated_at, message_count} |
| Ownership | SummaryService (application layer, written by generate_conversation_summary Celery task) |
| Failover Behavior | On cache miss, the summary is regenerated via LLM or falls back to extractive summarization. On Redis node failure, summaries are regenerated on every request (degraded latency). |

## 9.9 Lock Keys

### lock:{resource}

| Field | Value |
|---|---|
| TTL | Configurable (default 10 seconds, max 60 seconds) |
| Purpose | Generic distributed lock for any resource that requires exclusive access across application instances. Used by sagas, scheduled tasks, and critical sections. Implements the Redlock algorithm for safety across multiple Redis nodes. |
| Eviction Strategy | No eviction -- TTL-based auto-release. Key deleted on explicit unlock via Lua script (atomic check-and-delete). |
| Data Type | String -- holds lock owner UUID and expiry timestamp in JSON: {owner, expires_at} |
| Ownership | DistributedLock service (infrastructure layer, used by all layers) |
| Failover Behavior | On lock acquisition failure, spin-wait with exponential backoff (100ms base, 1s max, 10 retries). On Redis node failure, the Redlock algorithm requires majority consensus -- if < 3 of 5 Redis nodes are reachable, lock acquisition is denied. The caller must fall back to optimistic concurrency or fail fast. |

### saga:{id}:lock

| Field | Value |
|---|---|
| TTL | 30 seconds (auto-release -- saga steps are fast) |
| Purpose | Saga execution lock that prevents concurrent execution of the same saga instance. Ensures exactly-one execution of each saga step even if multiple workers pick up the same saga event. |
| Eviction Strategy | No eviction -- TTL-based auto-release. Cleared on saga completion or compensation. |
| Data Type | String -- JSON object: {owner, step, expires_at} |
| Ownership | SagaCoordinator (application layer) |
| Failover Behavior | On lock acquisition failure, the saga step is retried by the Celery task after backoff. On Redis node failure, saga execution degrades to at-least-once (risk of double execution -- sagas must be idempotent or use compensating transactions). |

## 9.10 Worker Keys

### celery:worker:{name}:status

| Field | Value |
|---|---|
| TTL | 30 seconds (heartbeat interval + grace period) |
| Purpose | Worker heartbeat and status key. Updated by each Celery worker on every heartbeat tick. Stores worker metadata: hostname, pool size, active tasks, queue subscriptions, and last heartbeat timestamp. Used by monitoring to detect dead/unhealthy workers. |
| Eviction Strategy | volatile-ttl -- expired keys indicate dead workers |
| Data Type | Hash -- fields: hostname, pool_size, active_tasks, reserved_tasks, queues[], last_heartbeat, worker_pid, celery_version, uptime_seconds |
| Ownership | CeleryWorkerMonitor (infrastructure layer, written by worker itself) |
| Failover Behavior | If a worker key expires (TTL exceeded without heartbeat), the monitoring system marks the worker as dead, alerts via PagerDuty, and redistributes its queues to healthy workers. On Redis node failure, worker monitoring is degraded -- all workers appear healthy until Redis is restored. Kubernetes liveness probes provide a secondary health check. |

## 9.11 TTL Summary Table

The following table consolidates every TTL value defined across all Redis keys in the blueprint:

| # | Key Pattern | TTL | Category |
|---|---|---|---|
| 1 | conversation:{id} | 1 hour (extended on read/write) | Conversation |
| 2 | conversation:{id}:messages | 1 hour (extended on append) | Conversation |
| 3 | conversation:{id}:lock | 30 seconds | Conversation |
| 4 | conversation:{id}:context | 5 minutes | Conversation |
| 5 | session:{id} | 24 hours (extended on request) | Identity |
| 6 | identity:{user_id} | 10 minutes | Identity |
| 7 | memory:{user_id} | 2 hours (extended on operation) | Memory |
| 8 | memory:{user_id}:confirmations | 15 minutes | Memory |
| 9 | meeting-lock:{id} | 10 seconds | Meeting |
| 10 | meeting:availability:{date} | 30 seconds | Meeting |
| 11 | meeting:calendar:{user} | 2 minutes | Meeting |
| 12 | idempotency:{key} | 24 hours | Idempotency |
| 13 | rate-limit:{user}:{endpoint} | Window-dependent (1s, 1m, 1h) | Rate Limiting |
| 14 | rate-limit:{ip}:{endpoint} | Window-dependent (1s, 1m, 1h) | Rate Limiting |
| 15 | tool-cache:{hash} | 30 minutes (configurable) | Cache |
| 16 | knowledge:search:{hash} | 5 min / 30 sec (filtered) | Cache |
| 17 | prompt:active:{context} | 1 hour (invalidated on promote) | Cache |
| 18 | summary:{conversation_id} | 1 hour | Cache |
| 19 | lock:{resource} | 10 seconds (configurable, max 60) | Lock |
| 20 | saga:{id}:lock | 30 seconds | Lock |
| 21 | celery:worker:{name}:status | 30 seconds | Worker |


# 11. Folder Ownership

Maps every folder in the project tree to its owner layer, allowed/forbidden imports, and dependency direction. All paths are relative to the project root.

---

## 11.1 Folder Ownership Table

| Folder | Owner | Can Access | Allowed Imports | Forbidden Imports | Dependency Direction |
| --- | --- | --- | --- | --- | --- |
| api/routes/ | Interface Adapters | api/middleware/, application/, config/ | application/, config/, middleware/ | domain/, infrastructure/, agents/, tools/ | Outward → Application Layer |
| api/middleware/ | Interface Adapters | api/routes/, config/, services/ | config/, services/ (identity) | domain/, infrastructure/, agents/ | Outward → API Routes |
| application/services/ | Application | domain/, application/handlers/, services/, config/ | domain/, services/, config/, application/events | infrastructure/, api/, agents/, tools/ | Outward → Domain Layer |
| application/handlers/commands/ | Application | application/services/, domain/, config/ | application/services/, domain/, config/ | infrastructure/, api/, agents/, tools/ | Outward → Domain Layer |
| application/handlers/queries/ | Application | application/dtos/, infrastructure/database/, infrastructure/cache/, config/ | application/dtos/, infrastructure/database/, infrastructure/cache/, config/ | domain/, agents/, tools/ | Lateral → Infrastructure (read models) |
| application/dtos/ | Application | domain/ (value objects for mapping) | domain/ (value objects only) | infrastructure/, api/, agents/, tools/ | Leaf — data transfer only |
| application/mappers/ | Application | domain/, application/dtos/ | domain/, application/dtos/ | infrastructure/, api/, agents/, tools/ | Outward → DTOs |
| domain/aggregates/ | Domain | domain/entities/, domain/value_objects/, domain/events/, domain/services/ | domain/entities/, domain/value_objects/, domain/events/, domain/services/ | EVERYTHING outside domain/ | Inward — zero external deps |
| domain/entities/ | Domain | domain/value_objects/, domain/events/ | domain/value_objects/, domain/events/ | EVERYTHING outside domain/ | Inward |
| domain/value_objects/ | Domain | None | None | EVERYTHING outside domain/ | Leaf — no dependencies |
| domain/services/ | Domain | domain/aggregates/, domain/entities/, domain/value_objects/, domain/events/, domain/specifications/, domain/policies/ | domain/* | EVERYTHING outside domain/ | Inward — within domain boundary |
| domain/events/ | Domain | domain/value_objects/, domain/aggregates/ | domain/value_objects/ | EVERYTHING outside domain/ | Inward — emitted outward |
| domain/specifications/ | Domain | domain/value_objects/, domain/entities/ | domain/value_objects/, domain/entities/ | EVERYTHING outside domain/ | Inward |
| domain/policies/ | Domain | domain/services/, domain/value_objects/ | domain/* | EVERYTHING outside domain/ | Inward |
| infrastructure/database/ | Infrastructure | config/, domain/ (interfaces only), repositories/ | config/, domain/ (repository interfaces) | api/, application/, agents/, tools/ | Inward — implements Domain ports |
| infrastructure/cache/ | Infrastructure | config/ | config/ | domain/, api/, application/, agents/, tools/ | Inward |
| infrastructure/queue/ | Infrastructure | config/, domain/ (event interfaces) | config/, domain/ (event interfaces only) | api/, application/, agents/, tools/ | Inward |
| infrastructure/llm/ | Infrastructure | config/ | config/ | domain/, api/, application/, agents/, tools/ | Inward |
| infrastructure/vector/ | Infrastructure | config/ | config/ | domain/, api/, application/, agents/, tools/ | Inward |
| infrastructure/monitoring/ | Infrastructure | config/ | config/ | domain/, api/, application/, agents/ | Inward |
| infrastructure/health/ | Infrastructure | config/ | config/ | domain/, api/, application/, agents/ | Inward |
| repositories/ | Infrastructure | domain/ (repository interfaces), infrastructure/database/, config/ | domain/ (interfaces), infrastructure/database/, config/ | api/, application/, agents/, tools/ | Inward — implements Domain ports |
| services/ | Application | domain/, application/events/, config/ | domain/, application/events/, config/ | infrastructure/, api/, agents/, tools/ | Outward → Domain Layer |
| agents/ | Agent Layer | domain/, services/, tools/, memory/, rag/, config/ | domain/, services/, tools/, memory/, rag/, config/ | infrastructure/, api/, repositories/ | Lateral → Application / Domain |
| memory/short_term/ | Infrastructure | config/ | config/ | api/, agents/, tools/, domain/ | Inward |
| memory/long_term/ | Infrastructure | config/, domain/ (interfaces), infrastructure/database/ | config/, domain/ (interfaces), infrastructure/database/ | api/, agents/, tools/ | Inward |
| memory/semantic/ | Infrastructure | config/, infrastructure/vector/ | config/, infrastructure/vector/ | api/, agents/, tools/, domain/ | Inward |
| rag/ | AI/ML Layer | config/, infrastructure/llm/, infrastructure/vector/ | config/, infrastructure/ (llm client, vector store) | api/, application/, domain/ | Outward → Infrastructure |
| tools/ | Agent Layer | domain/, services/, config/ | domain/, services/, config/ | infrastructure/, api/, agents/ | Outward → Domain / Application |
| workflows/ | Integration Layer | config/, infrastructure/ (http client) | config/, infrastructure/ (http client) | domain/, application/, agents/ | Outward → Infrastructure |
| tasks/ | Infrastructure | application/, services/, infrastructure/ | application/, services/, infrastructure/ | api/, agents/, domain/ | Outward → Application / Infra |
| monitoring/ | Infrastructure | config/ | config/ | domain/, application/, agents/ | Inward |
| config/ | Foundation | None | None | domain/, infrastructure/, api/ | Leaf — no dependencies |
| prompts/ | AI/ML Layer | config/ | config/ | domain/, infrastructure/, api/ | Inward → Foundation |
| tests/ | Quality | All packages | All packages (test deps only) | Production code paths | Everywhere — test only |

---

## 11.2 Dependency Tree (Import Flow)

Dependencies flow top-to-bottom. Arrows point from importer to imported package. Layers are grouped by horizontal bars.

    ┌──────────────────────────────────────────────────────────────────────────┐
    │                          config/ (Foundation)                           │
    │                      No dependencies — leaf node                        │
    └───────┬────────────────────────────┬────────────────────────────────────┘
            │                            │
            ▼                            ▼
    ┌───────────────┐           ┌──────────────────┐
    │  monitoring/  │           │  prompts/        │
    │  (Infra)      │           │  (AI/ML)         │
    └───────┬───────┘           └────────┬─────────┘
            │                            │
            ▼                            ▼
    ┌──────────────────────────────────────────────────────────────────────────┐
    │                         domain/ (Core Domain)                           │
    │  aggregates ← entities ← value_objects (leaf)                          │
    │  services ← aggregates                                                 │
    │  events ← value_objects                                                │
    │  specifications ← entities + value_objects                             │
    │  policies ← services + value_objects                                   │
    │  Zero external dependencies — pure Python                              │
    └───────┬───────┬───────┬───────┬───────┬───────┬───────┬────────┬───────┘
            │       │       │       │       │       │       │        │
            ▼       ▼       ▼       ▼       ▼       ▼       ▼        ▼
    ┌──────────────────────────────────────────────────────────────────────────┐
    │                     application/ + services/ (Application)              │
    │  services/ → domain/ (orchestrates domain objects)                     │
    │  handlers/commands/ → services/ + domain/                              │
    │  handlers/queries/ → dtos/ + infrastructure/database/ + cache/         │
    │  dtos/ → domain/value_objects (read-only)                              │
    │  mappers/ → domain/ + dtos/                                            │
    └───────┬───────┬───────┬───────┬───────┬───────┬───────┬────────┬───────┘
            │       │       │       │       │       │       │        │
            ▼       ▼       ▼       ▼       ▼       ▼       ▼        ▼
    ┌──────────────────────────────────────────────────────────────────────────┐
    │                  api/ (Interface Adapters) + middleware/                │
    │  routes/ → application/ + config/ + middleware/                        │
    │  middleware/ → config/ + services/ (identity)                          │
    │  No direct access to domain/, infrastructure/, agents/, tools/         │
    └───────┬───────┬───────┬───────┬───────┬───────┬───────┬────────┬───────┘
            │       │       │       │       │       │       │        │
            ▼       ▼       ▼       ▼       ▼       ▼       ▼        ▼
    ┌──────────────────────────────────────────────────────────────────────────┐
    │             infrastructure/ + repositories/ (Infrastructure)             │
    │  database/ → config/ + domain/interfaces                                │
    │  cache/, queue/, llm/, vector/ → config/                               │
    │  repositories/ → domain/interfaces + infrastructure/database/           │
    │  tasks/ → application/ + services/ + infrastructure/                    │
    └───────┬───────┬───────┬───────┬───────┬───────┬───────┬────────┬───────┘
            │       │       │       │       │       │       │        │
            ▼       ▼       ▼       ▼       ▼       ▼       ▼        ▼
    ┌──────────────────────────────────────────────────────────────────────────┐
    │    memory/ + rag/ (AI/ML + Infrastructure)                              │
    │  memory/short_term/ → config/                                          │
    │  memory/long_term/ → config/ + domain/interfaces + infra/database/     │
    │  memory/semantic/ → config/ + infra/vector/                            │
    │  rag/ → config/ + infra/llm/ + infra/vector/                           │
    └───────┬───────┬───────┬───────┬───────┬───────┬───────┬────────┬───────┘
            │       │       │       │       │       │       │        │
            ▼       ▼       ▼       ▼       ▼       ▼       ▼        ▼
    ┌──────────────────────────────────────────────────────────────────────────┐
    │         agents/ + tools/ + workflows/ (Agent + Integration Layers)      │
    │  agents/ → domain/ + services/ + tools/ + memory/ + rag/ + config/     │
    │  tools/ → domain/ + services/ + config/                                │
    │  workflows/ → config/ + infrastructure/ (http client)                  │
    └──────────────────────────────────────────────────────────────────────────┘
            │
            ▼
    ┌──────────────────────────────────────────────────────────────────────────┐
    │                          tests/ (Quality)                               │
    │  Imports EVERYTHING (test deps only). Never imported by any other       │
    │  package.                                                               │
    └──────────────────────────────────────────────────────────────────────────┘

**Legend**

    config/ (Foundation)     — leaf dependency, read by all layers
    domain/                  — zero external deps, imported by all upper layers
    application/ + services/ — orchestrates domain, consumed by api/
    api/ + middleware/       — outermost ring, imports application/ only
    infrastructure/          — implements domain ports, consumed by tasks/
    memory/ + rag/           — AI data layer, consumed by agents/
    agents/ + tools/         — top of the dependency chain, consumes everything
    tests/                   — universal importer, never imported

**Golden Rules**

    Domain/  →  must never import infrastructure/, api/, config/, agents/, tools/
    Api/     →  must never import domain/, infrastructure/, agents/, tools/
    Infra/   →  must never import api/, application/, agents/, tools/
    Config/  →  must never import domain/, infrastructure/, api/
    Agents/  →  must never import infrastructure/, api/, repositories/
    Tests/   →  may import any package but must never be imported by production code

# 12. Dependency Rules

This section defines strict dependency rules for every layer and package in the system. Violations are detected at compile time, lint time, or runtime with explicit enforcement mechanisms.

---

## 12.1 Dependency Enforcement Table

Each rule specifies a source layer/package, a target layer/package, the allowed direction, the consequence of violation, the detection mechanism, and the enforcement level.

### Layer Rules

| Rule # | Source Layer | Target Layer | Direction | Violation Consequence | Detection Mechanism | Enforcement Level |
|--------|-------------|-------------|-----------|----------------------|--------------------|--------------------|
| 1 | API | Application | Application -> Domain -> Infrastructure | Application depends on API | Build failure | Compile (mypy strict) |
| 1* | Application | Domain | One-way inward only | Domain imports Application | Build failure | Compile (mypy strict) |
| 1* | Domain | Infrastructure | Domain imports Infrastructure | Build failure | Compile (import-linter) |
| 2 | Infrastructure | API | Never | API layer imports Infrastructure directly | CI pipeline rejection | Lint (import-linter) |
| 3 | Application | API | Never | Application layer imports API package | Code review rejection | Lint (import-linter) |
| 4 | Domain | Application | Never | Domain imports Application package | Compile error | Compile (mypy strict) |
| 5 | Domain | Infrastructure | Never | Domain imports Infrastructure package | Compile error | Compile (mypy strict) |
| 6 | Domain | FastAPI, Celery, Redis, SQLAlchemy, httpx | Never | Domain imports an external framework | ImportError at module load | Runtime (import hook) |

### Package Rules

| Rule # | Source Package | Target Package | Direction | Violation Consequence | Detection Mechanism | Enforcement Level |
|--------|---------------|---------------|-----------|----------------------|--------------------|--------------------|
| 7 | domain/repository interfaces | infrastructure/repository impl | domain/ -> infrastructure/ | Infrastructure does not implement domain interface | Test failure in pytest-arch | Lint (pytest-arch) |
| 8 | infrastructure/repository impl | api/controllers | Never | Controller imports repository impl directly | CI pipeline rejection | Lint (import-linter) |
| 9 | infrastructure/repository impl | application/services | Never | Application service imports repository impl | Code review rejection | Lint (import-linter) |
| 10 | api/dtos | domain/entities | api/dtos -> domain/entities (mapping only) | DTO leaks domain entity to API response | Lint warning | Lint (ruff) |
| 11 | domain/entities | api/response dtos | Never | Domain entity used directly as API response schema | Build failure | Compile (mypy strict) |
| 12 | application/event handlers | domain/events | application/ -> domain/ | Event handler imports infrastructure queue directly | Test failure | Lint (pytest-arch) |
| 13 | application/event handlers | tasks/celery definitions | Never | Event handler references Celery task function directly | Code review rejection | Lint (import-linter) |
| 14 | application/services | domain/services, aggregates | application/ -> domain/ | Service imports database session directly | Build failure | Compile (mypy strict) |
| 15 | application/services | database, redis, celery | Never | Service uses ORM or Redis client directly | CI pipeline rejection | Lint (import-linter) |

### Cross-Cutting Rules

| Rule # | Source | Target | Direction | Violation Consequence | Detection Mechanism | Enforcement Level |
|--------|--------|--------|-----------|----------------------|--------------------|--------------------|
| 16 | config/ | ALL layers | config/ -> ALL (DI only) | Config accessed via global import instead of DI | Lint error | Lint (ruff INP001) |
| 17 | monitoring/ | Infrastructure layer only | monitoring/ -> infra/ | API layer imports monitoring internals | CI pipeline rejection | Lint (import-linter) |
| 18 | tests/ | ALL packages | tests/ -> ANY (test doubles required) | Test calls external service without mock | Test failure | Runtime (pytest) |
| 19 | shared kernel packages | N/A | All packages | Shared package missing __all__ | Lint warning | Lint (ruff) |
| 20 | ALL packages | ALL packages | No circular imports | Circular import detected | ImportError or lint error | Compile + Lint (ruff, mypy) |

---

## 12.2 Dependency Enforcement Diagram

The ASCII diagram below visualises the strict one-way dependency flow across all layers. Arrows point from dependent to dependency. Dashed lines indicate forbidden paths.

    Application Layer (app/)
    +----------------------------------------------+
    | Command Handlers  | Query Handlers           |
    | Event Handlers    | Application Services     |
    | DTOs              | Mappers                  |
    +--------+-----------------------------+-------+
             |                             |
             | depends on                  | depends on
             v                             v
    +--------+-----------------------------+-------+
    |             Domain Layer (domain/)            |
    | Aggregates   | Entities   | Value Objects    |
    | Domain Svcs  | Events     | Repository Intf  |
    | Specifications | Policies | Invariants       |
    +--------+-----------------------------+-------+
             |                             |
             | implements                  | depends on
             v                             v
    +--------+-----------------------------+-------+
    |         Infrastructure Layer (infra/)         |
    | Repository Impl  | DB Session   | Redis       |
    | Celery Tasks     | LLM Clients  | Vector Store |
    | Monitoring       | Health Checks              |
    +--------+-----------------------------+-------+
             ^
             |
    +--------+-----------------------------+-------+
    |              API Layer (api/)                 |
    | Routes     | Middleware  | Request/Response   |
    | Auth       | Rate Limit  | OpenAPI Schema    |
    +----------------------------------------------+

    Forbidden dependency paths (enforced at compile/lint time):

    api/  -X->  infrastructure/     (Rule 2)
    app/  -X->  api/                (Rule 3)
    domain/ -X->  app/              (Rule 4)
    domain/ -X->  infrastructure/   (Rule 5)
    domain/ -X->  FastAPI/Celery/   (Rule 6)
            Redis/SQLAlchemy/httpx
    infra/repo -X-> api/controllers (Rule 8)
    infra/repo -X-> app/services    (Rule 9)
    app/handlers -X-> tasks/        (Rule 13)
    app/services -X-> database/     (Rule 15)
            Redis/ Celery directly

    Legend:
      -->  allowed dependency (one-way, strict)
      -X-> forbidden dependency (zero tolerance)
      DI   dependency injection only (no direct import)

---

## 12.3 Enforcement Tools and Configuration

### mypy strict (compile-time)

Mypy is configured with --strict flag to enforce type purity at layer boundaries.

    # pyproject.toml
    [tool.mypy]
    strict = true
    disallow_any_unimported = true
    disallow_any_expr = true
    disallow_subclassing_any = true
    no_implicit_optional = true
    warn_unused_ignores = true
    warn_redundant_casts = true
    warn_return_any = true
    warn_unreachable = true

    # Per-layer overrides prevent domain from importing infrastructure
    [[tool.mypy.overrides]]
    module = ["domain.*", "domain.*"]
    ignore_errors = false
    disallow_any_imports = true
    follow_imports = "error"

Enforcement:
- Rule 6: domain package configured with disallow_any_imports = true and ollow_imports = 'error'. Any import of FastAPI, Celery, Redis, SQLAlchemy, or httpx in domain/ raises a compile error.
- Rule 11: domain entities annotated with @dataclass or Entity base class. API response DTOs use pydantic.BaseModel. Mypy strict mode catches if a domain entity is passed where a Pydantic model is expected.

### ruff (lint-time)

Ruff enforces import ordering, __all__ declarations, and forbidden imports via a custom plugin.

    # pyproject.toml
    [tool.ruff.lint]
    select = [
        "I",    # isort
        "INP",  # implicit namespace package
        "A",    # builtins shadowing
        "PLC",  # pylint convention
        "PLE",  # pylint error
        "PLR",  # pylint refactor
        "PLW",  # pylint warning
        "RUF",  # ruff-specific
    ]

    [tool.ruff.lint.per-file-ignores]
    "domain/*.py" = ["I001"]  # domain has zero external imports except standard lib

    # Custom forbidden import rules using ruff's flake8-tidy-imports
    [tool.ruff.lint.flake8-tidy-imports]
    ban-imports = [
        # Rule 16: config must come from DI only
        "from config import *",
        # Rule 15: no direct DB access in application
        "from sqlalchemy",
        "from redis",
        "from celery",
        # Rule 6: domain must not import infrastructure
        "from fastapi",
        "from httpx",
        "domain.*.from fastapi",
        "domain.*.from sqlalchemy",
        "domain.*.from celery",
        "domain.*.from redis",
        "domain.*.from httpx",
    ]

Enforcement:
- Rule 10: INP001 catches missing __all__ in shared kernel packages.
- Rule 16: an-imports catches direct imports from config.

### import-linter (lint-time)

Import-linter enforces layer boundaries with a declarative contract.

    # .import-linter
    [import_linter]
    root_packages = ["api", "application", "domain", "infrastructure"]

    [[import_linter.contracts]]
    name = "Layer Dependency Rule (Rule 1)"
    type = "layers"
    layers = [
        "api",
        "application",
        "domain",
        "infrastructure",
    ]
    contain_ok = false
    is_strict = true

    [[import_linter.contracts]]
    name = "Infrastructure must not depend on API (Rule 2)"
    type = "forbidden"
    source_modules = ["infrastructure"]
    forbidden_modules = ["api"]

    [[import_linter.contracts]]
    name = "Application must not depend on API (Rule 3)"
    type = "forbidden"
    source_modules = ["application"]
    forbidden_modules = ["api"]

    [[import_linter.contracts]]
    name = "Domain must not depend on Application (Rule 4)"
    type = "forbidden"
    source_modules = ["domain"]
    forbidden_modules = ["application"]

    [[import_linter.contracts]]
    name = "Domain must not depend on Infrastructure (Rule 5)"
    type = "forbidden"
    source_modules = ["domain"]
    forbidden_modules = ["infrastructure"]

    [[import_linter.contracts]]
    name = "Repository impl must not depend on API controllers (Rule 8)"
    type = "forbidden"
    source_modules = ["infrastructure.repositories"]
    forbidden_modules = ["api"]

    [[import_linter.contracts]]
    name = "Repository impl must not depend on Application services (Rule 9)"
    type = "forbidden"
    source_modules = ["infrastructure.repositories"]
    forbidden_modules = ["application"]

    [[import_linter.contracts]]
    name = "Event handlers must not depend on Celery tasks (Rule 13)"
    type = "forbidden"
    source_modules = ["application.event_handlers"]
    forbidden_modules = ["tasks"]

    [[import_linter.contracts]]
    name = "Application services must not depend on Infrastructure directly (Rule 15)"
    type = "forbidden"
    source_modules = ["application.services"]
    forbidden_modules = ["infrastructure.database", "infrastructure.redis", "infrastructure.celery"]

Enforcement:
- Rules 2-5, 8-9, 13, 15: Each is a dedicated orbidden contract that fails the lint step.
- Rule 1: The layers contract enforces the full one-way dependency chain.

### pytest-arch (test-time)

Architectural tests run as part of the test suite to verify package boundaries programmatically.

    # tests/architecture/test_dependency_rules.py
    
    from pytest_arch import ArchRule
    
    class TestDependencyRules:
    
        def test_repository_impl_implements_domain_interface(self, arch):
            (ArchRule()
             .classes_that("are in", "infrastructure.repositories")
             .should()
             .implement("domain.repositories.*")
             .check(arch))
    
        def test_event_handlers_depend_on_domain_events(self, arch):
            (ArchRule()
             .classes_that("are in", "application.event_handlers")
             .should()
             .depend_only_on("domain.events")
             .check(arch))
    
        def test_services_depend_on_domain_aggregates(self, arch):
            (ArchRule()
             .classes_that("are in", "application.services")
             .should()
             .depend_only_on("domain", "config")
             .check(arch))
    
        def test_tests_mock_external_services(self, arch):
            (ArchRule()
             .classes_that("are in", "tests")
             .should()
             .not_depend_on("infrastructure.llm")
             .and_should()
             .not_depend_on("infrastructure.database")
             .check(arch))

Enforcement:
- Rule 7: Verifies every repository implementation has a matching domain interface.
- Rule 12: Verifies event handlers only depend on domain events.
- Rule 14: Verifies application services only depend on domain and config.
- Rule 18: Tests are allowed to import anything but must not import production infrastructure directly (enforced via test-only dependency injection).

### CI Pipeline Checks

All enforcement runs in the CI pipeline as separate stages:

    Stage 1: compile (mypy strict)
    Stage 2: lint (ruff + import-linter)
    Stage 3: arch-test (pytest-arch)
    Stage 4: unit + integration tests (pytest)

    Pipeline fails immediately at Stage 1 if any layer-boundary mypy error
    is detected. Stage 2 catches import violations not visible to mypy
    (e.g., runtime imports). Stage 3 validates structural architecture rules.
    Stage 4 catches mock violations and integration policy breaches.

    A dependency rule violation at any stage blocks merge to main and
    requires a waiver from the architecture review board.

### Runtime Import Hook (last resort)

For Rule 6 specifically, a runtime import hook is registered during application startup to catch any domain-level import of forbidden packages that slipped through static analysis:

    # infrastructure/bootstrap/hooks.py
    
    import sys
    
    FORBIDDEN_IN_DOMAIN = {"fastapi", "celery", "redis", "sqlalchemy", "httpx"}
    
    class DomainImportBlocker:
        def find_spec(self, fullname, path, target=None):
            if not fullname:
                return None
            parts = fullname.split(".")
            for forbidden in FORBIDDEN_IN_DOMAIN:
                if forbidden in parts:
                    caller_frame = sys._getframe(1)
                    caller_module = caller_frame.f_globals.get("__name__", "")
                    if caller_module.startswith("domain"):
                        raise ImportError(
                            f"Rule 6 violation: domain module {caller_module} "
                            f"attempted to import {fullname}. "
                            f"Domain must not import {forbidden}."
                        )
            return None
    
    sys.meta_path.insert(0, DomainImportBlocker())

This hook is registered in the application entry point during development and CI test runs. It is disabled in production for performance reasons.

---

## 12.4 Summary

    Enforcement Level   | Tools Used                    | Rules Covered
    --------------------|-------------------------------|--------------
    Compile             | mypy strict                   | 1, 4, 5, 6, 11, 14
    Lint                | ruff + import-linter          | 2, 3, 8, 9, 10, 12, 13, 15, 16, 17, 19, 20
    Test                | pytest-arch                   | 7, 12, 14, 18
    Runtime             | Import hook (dev only)        | 6
    CI Pipeline         | All of the above              | All 20 rules

    All 20 rules are enforced automatically. Zero exceptions are permitted
    without a signed architecture waiver.


# 10. Database Ownership Matrix

This section maps every database table to its owning aggregate, defining the full lifecycle from creation through retention, archival, and purging. Each row establishes a single point of ownership — no table is mutated by more than one aggregate. Cross-aggregate reads are permitted only through read models or internal APIs.

## 10.1 Database Schema Ownership Groups

The diagram below shows which aggregate owns which tables. Arrows indicate foreign key dependencies, not data flow.

    ┌──────────────────────────────────────────────────────────────────────────────────────────────────────┐
    │  Database Schema Ownership Groups                                                                     │
    │                                                                                                      │
    │  ┌──────────────────────────┐    ┌─────────────────────────────┐    ┌──────────────────────────────┐  │
    │  │  UserProfile Aggregate   │    │  Conversation Aggregate     │    │  Meeting Aggregate           │  │
    │  │                          │    │                             │    │                              │  │
    │  │  users (root)            │    │  conversations (root)        │    │  meetings (root)              │  │
    │  │  user_preferences        │───▶│  conversation_messages       │    │  meeting_history              │  │
    │  │  sessions                │    │  long_term_memory            │    │  meeting_availability_cache   │  │
    │  └──────────────────────────┘    │  memory_confirmations        │    └──────────────────────────────┘  │
    │                                  └─────────────────────────────┘                                      │
    │                                                                                                      │
    │  ┌──────────────────────────┐    ┌─────────────────────────────┐    ┌──────────────────────────────┐  │
    │  │  Lead Aggregate          │    │  KnowledgeDocument Aggregate│    │  WorkflowExecution Aggregate │  │
    │  │                          │    │                             │    │                              │  │
    │  │  leads (root)            │    │  knowledge_documents (root)  │    │  workflow_executions (root)  │  │
    │  │  lead_activities         │    │  document_chunks             │    │  saga_step_logs              │  │
    │  └──────────────────────────┘    │  embeddings                  │    └──────────────────────────────┘  │
    │                                  └─────────────────────────────┘                                      │
    │                                                                                                      │
    │  ┌──────────────────────────┐    ┌─────────────────────────────┐    ┌──────────────────────────────┐  │
    │  │  Notification Aggregate  │    │  PromptVersion Aggregate    │    │  Cross-Cutting (No Owner)    │  │
    │  │                          │    │                             │    │                              │  │
    │  │  notifications (root)    │    │  prompt_versions (root)     │    │  analytics_events             │  │
    │  │  delivery_attempts       │    │  prompt_test_results        │    │  audit_logs                   │  │
    │  └──────────────────────────┘    └─────────────────────────────┘    └──────────────────────────────┘  │
    │                                                                                                      │
    │  Foreign Key Direction: Users ▼  Conversations ▼  Leads ▼  Meetings ▼  Workflows                     │
    │                          All cross-table FK references point toward the owning aggregate's root.     │
    └──────────────────────────────────────────────────────────────────────────────────────────────────────┘

## 10.2 Table Ownership Matrix

### users

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | UserProfile |
| Repository | UserProfileRepository |
| Primary Key Strategy | UUID v4 (user_id) |
| Indexes | email (UNIQUE), tenant_id + status, created_at, last_login_at, role |
| Foreign Keys | tenant_id → tenants.tenant_id |
| Events | UserRegistered, UserProfileUpdated, UserDeactivated |
| Retention Policy | Indefinite (core identity record) |
| Archive Strategy | Anonymize after 7 years of inactivity; delete anonymized record after 10 years |
| Partition Strategy | BY tenant_id (list partitioning) |
| Sensitive Columns | email, hashed_password, phone, full_name, avatar_url |

### user_preferences

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | UserProfile |
| Repository | UserProfileRepository (accessed through UserProfile aggregate) |
| Primary Key Strategy | user_id (UUID, same as users PK — 1:1 relationship) |
| Indexes | user_id (PK/FK) |
| Foreign Keys | user_id → users.user_id ON DELETE CASCADE |
| Events | UserPreferencesChanged |
| Retention Policy | Indefinite (tied to user lifecycle) |
| Archive Strategy | Bundled with user record; archived and anonymized together |
| Partition Strategy | BY tenant_id (inherited from users via FK) |
| Sensitive Columns | timezone, locale, notification_settings (low sensitivity) |

### conversations

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | Conversation |
| Repository | ConversationRepository |
| Primary Key Strategy | UUID v4 (conversation_id) |
| Indexes | user_id + created_at, status, last_activity_at, tenant_id |
| Foreign Keys | user_id → users.user_id, tenant_id → tenants.tenant_id |
| Events | ConversationCreated, ConversationArchived |
| Retention Policy | 90 days active; 365 days archived |
| Archive Strategy | Move to cold storage (S3 Glacier / Azure Archive) after 365 days; soft-delete marker in primary DB |
| Partition Strategy | BY tenant_id (list) + RANGE BY created_at (monthly sub-partitions) |
| Sensitive Columns | title, metadata |

### conversation_messages

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | Conversation |
| Repository | ConversationRepository (accessed through Conversation aggregate only) |
| Primary Key Strategy | UUID v4 (message_id) |
| Indexes | conversation_id + created_at, conversation_id + role, tenant_id |
| Foreign Keys | conversation_id → conversations.conversation_id ON DELETE CASCADE |
| Events | MessageAppended |
| Retention Policy | 90 days (active), 365 days (archived conversation messages) |
| Archive Strategy | Batch export to Parquet on S3 before deletion; compressed JSONL per conversation |
| Partition Strategy | BY conversation_id (hash) + RANGE BY created_at (monthly) |
| Sensitive Columns | content (user message text), metadata (may contain PII) |

### sessions

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | UserProfile |
| Repository | UserProfileRepository |
| Primary Key Strategy | UUID v4 (session_id) |
| Indexes | user_id, token (UNIQUE), expires_at, revoked_at |
| Foreign Keys | user_id → users.user_id ON DELETE CASCADE |
| Events | UserLoggedIn, UserLoggedOut |
| Retention Policy | TTL-based: 24h after expiry; revoked sessions purged immediately |
| Archive Strategy | Not archived (transient; session tokens are security-sensitive and must be purged) |
| Partition Strategy | BY expires_at (monthly range) for efficient bulk deletion |
| Sensitive Columns | token, refresh_token, ip_address, user_agent |

### meetings

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | Meeting |
| Repository | MeetingRepository |
| Primary Key Strategy | UUID v4 (meeting_id) |
| Indexes | organizer_id + start_time, status, participant_ids (GIN for JSONB array), tenant_id |
| Foreign Keys | organizer_id → users.user_id, tenant_id → tenants.tenant_id |
| Events | MeetingScheduled, MeetingStarted, MeetingEnded, MeetingCancelled |
| Retention Policy | 365 days after meeting end date |
| Archive Strategy | Move to cold storage after 365 days; transcript remaining accessible via flag |
| Partition Strategy | BY tenant_id (list) + RANGE BY start_time (monthly) |
| Sensitive Columns | title, description, conference_url, recording_url |

### meeting_history

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | Meeting |
| Repository | MeetingRepository (accessed through Meeting aggregate) |
| Primary Key Strategy | UUID v4 (history_id) |
| Indexes | meeting_id + changed_at, changed_by, change_type |
| Foreign Keys | meeting_id → meetings.meeting_id ON DELETE CASCADE, changed_by → users.user_id |
| Events | MeetingHistoryRecorded (part of aggregate event chain) |
| Retention Policy | 365 days (same as parent meeting) |
| Archive Strategy | Bundled with meeting archival; exported as JSON array in meeting archive |
| Partition Strategy | BY meeting_id (hash) |
| Sensitive Columns | change_details (may contain scheduling notes, reasons for cancellation) |

### meeting_availability_cache

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | Meeting |
| Repository | MeetingRepository |
| Primary Key Strategy | Composite: (user_id, slot_date) |
| Indexes | user_id, slot_date, is_available |
| Foreign Keys | user_id → users.user_id |
| Events | None (cache-only table; rebuilt on miss) |
| Retention Policy | 30 days sliding window (future slots only) |
| Archive Strategy | Not archived (recomputable from meetings table; transient cache) |
| Partition Strategy | BY slot_date (weekly range) |
| Sensitive Columns | None |

### leads

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | Lead |
| Repository | LeadRepository |
| Primary Key Strategy | UUID v4 (lead_id) |
| Indexes | email (UNIQUE), status, score, assigned_to, captured_by, created_at, tenant_id |
| Foreign Keys | assigned_to → users.user_id, captured_by → users.user_id, tenant_id → tenants.tenant_id |
| Events | LeadCaptured, LeadQualified, LeadAssigned, LeadConverted, LeadDiscarded |
| Retention Policy | 730 days (2 years) after last activity |
| Archive Strategy | Export to CRM (Salesforce/HubSpot) before hard deletion; archive to cold storage for compliance |
| Partition Strategy | BY tenant_id (list) + RANGE BY created_at (monthly) |
| Sensitive Columns | email, phone, company_data, enrichment_data, social_profiles |

### lead_activities

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | Lead |
| Repository | LeadRepository (accessed through Lead aggregate) |
| Primary Key Strategy | UUID v4 (activity_id) |
| Indexes | lead_id + created_at, activity_type, performed_by |
| Foreign Keys | lead_id → leads.lead_id ON DELETE CASCADE, performed_by → users.user_id |
| Events | LeadActivityLogged (part of aggregate event chain) |
| Retention Policy | 730 days (same as parent lead) |
| Archive Strategy | Bundled with lead archival; exported as JSONL per lead |
| Partition Strategy | BY lead_id (hash) + RANGE BY created_at (monthly) |
| Sensitive Columns | activity_details (may contain PII in notes, call transcripts, email content) |

### long_term_memory

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | Conversation |
| Repository | MemoryRepository |
| Primary Key Strategy | UUID v4 (memory_id) |
| Indexes | user_id + field_name, conversation_id, created_at, (user_id, conversation_id) composite |
| Foreign Keys | user_id → users.user_id, conversation_id → conversations.conversation_id ON DELETE CASCADE |
| Events | MemoryUpdated, MemoryFieldConfirmed, MemoryEmbeddingUpdated |
| Retention Policy | 365 days (extended on every conversation activity) |
| Archive Strategy | Export as JSON before deletion; compressed memory snapshot per conversation |
| Partition Strategy | BY user_id (hash) |
| Sensitive Columns | field_value (all memory fields may contain PII), context |

### memory_confirmations

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | Conversation |
| Repository | MemoryRepository |
| Primary Key Strategy | UUID v4 (confirmation_id) |
| Indexes | user_id + conversation_id, token (UNIQUE), expires_at, status |
| Foreign Keys | user_id → users.user_id, conversation_id → conversations.conversation_id ON DELETE CASCADE |
| Events | MemoryUpdateRequested, MemoryFieldConfirmed |
| Retention Policy | 15 minutes (pending, TTL-based); 7 days (completed/expired) |
| Archive Strategy | Not archived (transient confirmation workflow data) |
| Partition Strategy | BY conversation_id (hash) |
| Sensitive Columns | staged_value (temporary unconfirmed memory value) |

### knowledge_documents

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | KnowledgeDocument |
| Repository | KnowledgeDocumentRepository |
| Primary Key Strategy | UUID v4 (document_id) |
| Indexes | owner_id, title (GIN for full-text search), tags (GIN), created_at, document_type, tenant_id |
| Foreign Keys | owner_id → users.user_id, tenant_id → tenants.tenant_id |
| Events | DocumentCreated, DocumentUpdated, DocumentDeleted, DocumentVersionCreated |
| Retention Policy | Indefinite (until explicitly deleted by owner) |
| Archive Strategy | Move to S3/Blob storage after 365 days of no access; restore on read (lazy restore) |
| Partition Strategy | BY tenant_id (list) + RANGE BY created_at (quarterly) |
| Sensitive Columns | content, title, description (may contain business-sensitive information) |

### document_chunks

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | KnowledgeDocument |
| Repository | KnowledgeDocumentRepository (accessed through KnowledgeDocument aggregate) |
| Primary Key Strategy | UUID v4 (chunk_id) |
| Indexes | document_id + chunk_index, document_id, chunk_hash |
| Foreign Keys | document_id → knowledge_documents.document_id ON DELETE CASCADE |
| Events | DocumentChunked (part of DocumentCreated/DocumentUpdated) |
| Retention Policy | Same as parent document |
| Archive Strategy | Bundled with parent document archival |
| Partition Strategy | BY document_id (hash) |
| Sensitive Columns | chunk_text (contains document content) |

### embeddings

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | KnowledgeDocument (document embeddings) / Conversation (memory embeddings) |
| Repository | KnowledgeDocumentRepository / MemoryRepository (polymorphic via entity_type) |
| Primary Key Strategy | Composite: (entity_type, entity_id, embedding_model, dimension) |
| Indexes | (entity_type, entity_id), vector (IVFFlat with cosine distance), embedding_model |
| Foreign Keys | Polymorphic FK: (entity_type, entity_id) references different tables based on entity_type |
| Events | DocumentEmbeddingGenerated, MemoryEmbeddingUpdated |
| Retention Policy | Same as parent entity (document or memory record) |
| Archive Strategy | Bundled with parent; vectors can be regenerated from source content |
| Partition Strategy | BY entity_type (list: 'document', 'memory', 'conversation') |
| Sensitive Columns | None (vectors are opaque float arrays; not human-readable) |

### workflow_executions

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | WorkflowExecution |
| Repository | WorkflowExecutionRepository |
| Primary Key Strategy | UUID v4 (execution_id) |
| Indexes | workflow_def_id, status, started_at, triggered_by, tenant_id |
| Foreign Keys | triggered_by → users.user_id, tenant_id → tenants.tenant_id |
| Events | WorkflowTriggered, WorkflowStepCompleted, WorkflowCompleted, WorkflowFailed, WorkflowCancelled |
| Retention Policy | 90 days (successful); 180 days (failed/compensated) |
| Archive Strategy | Compress and move to cold storage; failed executions retained longer for postmortem |
| Partition Strategy | BY tenant_id (list) + RANGE BY started_at (monthly) |
| Sensitive Columns | input_data, output_data, error_details, callback_url |

### saga_step_logs

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | WorkflowExecution |
| Repository | WorkflowExecutionRepository (accessed through WorkflowExecution aggregate) |
| Primary Key Strategy | UUID v4 (log_id) |
| Indexes | execution_id + step_name, execution_id + status, started_at |
| Foreign Keys | execution_id → workflow_executions.execution_id ON DELETE CASCADE |
| Events | WorkflowStepCompleted, WorkflowStepFailed, WorkflowStepCompensated |
| Retention Policy | 90 days (same as parent execution) |
| Archive Strategy | Bundled with parent execution archival |
| Partition Strategy | BY execution_id (hash) |
| Sensitive Columns | step_input, step_output, error_message, stack_trace |

### notifications

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | Notification |
| Repository | NotificationRepository |
| Primary Key Strategy | UUID v4 (notification_id) |
| Indexes | user_id + status, user_id + created_at, notification_type, tenant_id |
| Foreign Keys | user_id → users.user_id, tenant_id → tenants.tenant_id |
| Events | NotificationSent, NotificationRead, NotificationDismissed |
| Retention Policy | 30 days (delivered); 7 days (failed/undelivered) |
| Archive Strategy | Not archived (transient; delivery logs retained via delivery_attempts) |
| Partition Strategy | BY user_id (hash) + RANGE BY created_at (daily) |
| Sensitive Columns | title, body, deep_link (may contain PII or sensitive action links) |

### delivery_attempts

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | Notification |
| Repository | NotificationRepository (accessed through Notification aggregate) |
| Primary Key Strategy | UUID v4 (attempt_id) |
| Indexes | notification_id + channel, status, attempted_at |
| Foreign Keys | notification_id → notifications.notification_id ON DELETE CASCADE |
| Events | NotificationDelivered, NotificationFailed |
| Retention Policy | 30 days |
| Archive Strategy | Not archived (aggregate metrics retained; raw logs pruned) |
| Partition Strategy | BY notification_id (hash) |
| Sensitive Columns | provider_response (may contain push tokens, email headers, delivery receipts) |

### prompt_versions

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | PromptVersion |
| Repository | PromptVersionRepository |
| Primary Key Strategy | Composite: (prompt_id, version_number) |
| Indexes | prompt_id, version_number (UNIQUE per prompt), active, created_at |
| Foreign Keys | created_by → users.user_id |
| Events | PromptVersionCreated, PromptVersionPromoted, PromptVersionRolledBack |
| Retention Policy | Indefinite (full version history preserved) |
| Archive Strategy | Move versions older than 1 year and not currently active to cold storage; restore on version diff query |
| Partition Strategy | BY prompt_id (hash) |
| Sensitive Columns | prompt_content, system_prompt, model_config (may contain API keys in config) |

### prompt_test_results

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | PromptVersion |
| Repository | PromptVersionRepository (accessed through PromptVersion aggregate) |
| Primary Key Strategy | UUID v4 (result_id) |
| Indexes | (prompt_id, version_number), test_case, created_at, score |
| Foreign Keys | (prompt_id, version_number) → prompt_versions.(prompt_id, version_number) ON DELETE CASCADE |
| Events | PromptVersionEvaluated |
| Retention Policy | 90 days (raw results); aggregated metrics retained indefinitely |
| Archive Strategy | Aggregate metrics (avg_score, pass_rate) moved to analytics_events; raw test inputs/outputs archived to cold storage |
| Partition Strategy | BY prompt_id (hash) + RANGE BY created_at (monthly) |
| Sensitive Columns | test_input, test_output (may contain PII reproduced from test cases) |

### analytics_events

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | None (cross-cutting / Analytics subsystem) |
| Repository | AnalyticsRepository (read-model only; write-only event ingestion) |
| Primary Key Strategy | UUID v4 (event_id) |
| Indexes | event_type + created_at, user_id, tenant_id, session_id |
| Foreign Keys | user_id → users.user_id (nullable for anonymous), tenant_id → tenants.tenant_id |
| Events | None (this table IS the event store for analytics; events are not re-published) |
| Retention Policy | 90 days (raw events); 365 days (aggregated rollups) |
| Archive Strategy | Raw events exported to data lake (S3/Parquet/JSONL) after 90 days; partitioned by event_type + date |
| Partition Strategy | BY event_type (list) + RANGE BY created_at (daily; auto-partitioned by ClickHouse) |
| Sensitive Columns | event_payload (contains full event data; sensitive fields must be explicitly included via allowlist) |

### audit_logs

| Attribute | Value |
|-----------|-------|
| Owner Aggregate | None (cross-cutting / Security subsystem) |
| Repository | AuditRepository |
| Primary Key Strategy | UUID v4 (log_id) |
| Indexes | user_id, action, resource_type + resource_id, created_at, tenant_id, correlation_id |
| Foreign Keys | user_id → users.user_id (nullable for system actions) |
| Events | AuditEventRecorded |
| Retention Policy | 7 years (regulatory compliance: GDPR, SOC2, HIPAA) |
| Archive Strategy | Move to WORM (Write-Once-Read-Many) storage after 1 year; immutable append-only before archive |
| Partition Strategy | BY action_type (list: 'create', 'read', 'update', 'delete', 'auth', 'system') + RANGE BY created_at (monthly) |
| Sensitive Columns | All columns are sensitive by nature (audit trail is a record of all user and system actions) |

## 10.3 Retention Policy Summary

| Policy Name | Retention Period | Archive After | Hard Delete After | Applicable Tables |
|-------------|-----------------|---------------|-------------------|-------------------|
| Indefinite | Forever | N/A | N/A (until explicit delete) | users, user_preferences, knowledge_documents, prompt_versions |
| Transient | TTL-based (minutes to 24h) | N/A | Immediate after TTL | memory_confirmations (15m), sessions (24h after expiry) |
| Short | 7 days | N/A | Immediate | memory_confirmations (expired), delivery_attempts (failed) |
| Medium | 30 days | N/A | Immediate after retention | notifications, delivery_attempts, meeting_availability_cache |
| Active Archive | 90 days | 90 days | 365 days | conversations, conversation_messages, workflow_executions (successful), saga_step_logs, analytics_events (raw) |
| Extended | 180 days | 180 days | 365 days | workflow_executions (failed/compensated) |
| Long | 365 days | 365 days | 730 days | meetings, meeting_history, long_term_memory, knowledge_documents (inactive) |
| Compliance | 730 days (2 years) | 730 days | N/A (anonymize) | leads, lead_activities |
| Regulatory | 7 years | 1 year (to WORM) | 10 years (after WORM expiry) | audit_logs |
| Aggregated | 365 days (aggregates) | 365 days | N/A (aggregates retained) | analytics_events (aggregated rollups) |

## 10.4 Audit Trail Strategy

Audit trails are captured at three levels: domain event sourcing, explicit audit log records, and database-level auditing.

### Level 1: Event Sourcing (Implicit Audit)

Every domain event published by any aggregate is stored permanently in the event store (a dedicated event_store table not shown above because it is an infrastructure concern, not an aggregate-owned table). The event store provides:

    Event Store Schema:
        event_id        UUID        (PK)
        aggregate_type  VARCHAR(50) (e.g., 'Conversation', 'Meeting', 'Lead')
        aggregate_id    UUID        (the root ID)
        event_type      VARCHAR(100)(e.g., 'ConversationArchived')
        event_data      JSONB       (full event payload)
        metadata        JSONB       (correlation_id, causation_id, user_id, tenant_id)
        version         INTEGER     (aggregate version for concurrency)
        created_at      TIMESTAMPTZ (immutable, set once on append)

    The event store is append-only. No row is ever updated or deleted.
    Retention: 7 years (same as audit_logs).
    Archive: to WORM after 1 year.

### Level 2: Explicit Audit Logs (audit_logs table)

The audit_logs table captures security-relevant actions that do not correspond to domain events:

    Audit Log Entry Triggers:
        Authentication events:     login, logout, login_failed, password_reset, mfa_enabled
        Authorization events:      permission_granted, permission_revoked, role_changed
        Data access events:        export_requested, bulk_delete, admin_impersonation
        Configuration events:      feature_flag_toggled, tenant_plan_changed, rate_limit_modified
        System events:             service_restarted, migration_run, config_reloaded

    Audit Log Enrichment:
        Every audit entry is enriched with:
            correlation_id   (from the HTTP request or background job trigger)
            user_id          (resolved identity; NULL for system actions)
            tenant_id        (tenant context)
            ip_address       (for user-initiated actions)
            user_agent       (client identification)
            geo_location     (from IP, best-effort)

    Audit Log Immutability:
        Once written, audit_logs records are never updated or deleted.
        The archive to WORM storage after 1 year provides cryptographic
        proof of immutability (SHA-256 hash chain).
        Daily hash of the audit log table is published to a public
        transparency log (e.g., AWS CloudTrail Digest / Azure
        Immutable Blob).

### Level 3: Database-Level Auditing

In addition to application-level audit, PostgreSQL audit extensions provide a safety net:

    pgaudit Configuration:
        pgaudit.log = 'write,ddl,role'
        pgaudit.log_level = 'notice'
        pgaudit.log_relation = on
        pgaudit.log_catalog = off

    This captures all DDL (schema changes), DML writes (INSERT, UPDATE, DELETE)
    on all tables, and role/permission changes. These logs are shipped to the
    central log aggregator (ELK / Loki) with 90-day retention.

### Audit Trail Query Patterns

    Pattern 1: Who changed what on a specific resource?
        SELECT * FROM audit_logs
        WHERE resource_type = 'lead'
          AND resource_id = 'lead_abc123'
        ORDER BY created_at DESC;

    Pattern 2: All actions by a user in a time window?
        SELECT * FROM audit_logs
        WHERE user_id = 'user_xyz789'
          AND created_at BETWEEN '2026-06-01' AND '2026-06-30'
        ORDER BY created_at DESC;

    Pattern 3: All domain events for an aggregate?
        SELECT * FROM event_store
        WHERE aggregate_type = 'Meeting'
          AND aggregate_id = 'meeting_def456'
        ORDER BY version ASC;

    Pattern 4: Compliance export for a date range?
        SELECT * FROM audit_logs
        WHERE created_at BETWEEN '2026-01-01' AND '2026-12-31'
        ORDER BY created_at ASC
        LIMIT 10000;  -- paginate through for full export


# 14. Implementation Order

## Dependency Graph (ASCII)

`
    Phase 1: Foundation
    ┌─────────────────────────────────────────────────────────┐
    │  1. Scaffolding     2. Config       3. Logging         │
    │  4. Database        5. Redis        6. DI Container    │
    └──────────┬──────────────────────────────┬──────────────┘
               │                              │
               ▼                              ▼
    ┌────────────────────┐   ┌──────────────────────────────┐
    │ Phase 2: Domain    │◄──│ Phase 2: Infrastructure      │
    │  7. Aggregates     │   │ 10. Repository Impls         │
    │  8. Services       │   │ 11. Event Bus                │
    │  9. Interfaces     │   └──────────────────────────────┘
    └──────────┬─────────┘
               │
               ▼
    Phase 3: Application Layer
    ┌───────────────────────────────────────────────────────┐
    │ 12. Command Handlers  13. Query Handlers              │
    │ 14. App Services      15. DTOs & Mappers              │
    │ 16. Event Handlers    17. Celery Tasks               │
    │ 18. Saga Coordinator                                 │
    └──────────────────────────┬────────────────────────────┘
                               │
                               ▼
    Phase 4: API & Middleware
    ┌────────────────────────────────────────────────────────┐
    │ 19. Middleware Stack  20. Route Setup                  │
    │ 21. Endpoints         22. Validation                   │
    │ 23. API Documentation                                  │
    └──────────────────────────┬─────────────────────────────┘
                               │
                               ▼
    Phase 5: AI & Memory
    ┌─────────────────────────────────────────────────────────┐
    │ 24. LLM Client      25. Model Router                   │
    │ 26. Prompt Registry  27. Tool Registry                 │
    │ 28. Short-term Mem   29. Long-term Mem                 │
    │ 30. Semantic Mem     31. RAG Pipeline                  │
    │ 32. LangGraph Agent                                    │
    └──────────────────────────┬──────────────────────────────┘
                               │
                               ▼
    Phase 6: Integration & Operations
    ┌──────────────────────────────────────────────────────────┐
    │ 33. n8n Webhook     34. Celery Worker                   │
    │ 35. Saga Testing    36. Monitoring & Alerting           │
    │ 37. E2E Tests       38. Deployment Config               │
    │ 39. Security Audit  40. Production Review               │
    └──────────────────────────────────────────────────────────┘
`

## Phase 1 — Foundation (Week 1-2)

Dependency reasoning: Every subsequent step depends on these — no code can run without config, logging, DB, or Redis.

| # | Step | Effort (pd) | Prerequisites | Risk |
|---|------|-------------|---------------|------|
| 1 | Project scaffolding: folder structure, pyproject.toml, linter, formatter, mypy config | 1 | None | Low |
| 2 | Configuration: settings.py, .env template, feature flags | 1 | #1 | Low |
| 3 | Logging & monitoring: structured logging setup, health check stubs | 1 | #2 | Low |
| 4 | Database: migration tool setup, initial schema, connection pool | 2 | #1, #2, #3 | Medium |
| 5 | Redis: connection setup, Sentinel config (already done) | 0.5 | #2 | Low |
| 6 | Dependency injection: FastAPI app factory, dependency_overrides | 1.5 | #2, #3, #4, #5 | Medium |

## Phase 2 — Domain & Infrastructure (Week 2-3)

Dependency reasoning: Domain must exist before application services. Repositories need interfaces first, implementations second.

| # | Step | Effort (pd) | Prerequisites | Risk |
|---|------|-------------|---------------|------|
| 7 | Domain aggregates, entities, value objects | 3 | #6 | Medium |
| 8 | Domain services, domain events, specifications | 2 | #7 | Medium |
| 9 | Repository interfaces (domain layer) | 1 | #7 | Low |
| 10 | Repository implementations (infrastructure) | 2 | #4, #5, #9 | Medium |
| 11 | Event definitions and event bus | 1.5 | #8, #10 | Medium |

## Phase 3 — Application Layer (Week 3-4)

Dependency reasoning: Application depends on domain + infrastructure. Commands/queries need repositories and events.

| # | Step | Effort (pd) | Prerequisites | Risk |
|---|------|-------------|---------------|------|
| 12 | Command handlers | 3 | #8, #9, #10, #11 | High |
| 13 | Query handlers | 2 | #9, #10 | Medium |
| 14 | Application services | 2 | #12, #13 | Medium |
| 15 | DTOs and mappers | 1 | #7 | Low |
| 16 | Event handlers | 1.5 | #11, #14 | Medium |
| 17 | Celery task definitions | 1 | #5, #14 | Medium |
| 18 | Saga coordinator | 2 | #12, #14, #16 | High |

## Phase 4 — API & Middleware (Week 4-5)

Dependency reasoning: API depends on everything below it. Middleware must be in place before endpoints.

| # | Step | Effort (pd) | Prerequisites | Risk |
|---|------|-------------|---------------|------|
| 19 | Middleware stack: identity, auth, rate limit, request ID, error handler | 2 | #6 | High |
| 20 | Controller registration and route setup | 1 | #19 | Low |
| 21 | API endpoint implementation per aggregate | 3 | #14, #15, #20 | High |
| 22 | Request/response validation | 1 | #21 | Low |
| 23 | API documentation | 0.5 | #22 | Low |

## Phase 5 — AI & Memory (Week 5-6)

Dependency reasoning: AI layer depends on domain, application, and infrastructure. Memory needs repository, Redis, vector DB.

| # | Step | Effort (pd) | Prerequisites | Risk |
|---|------|-------------|---------------|------|
| 24 | LLM client (LiteLLM wrapper) | 2 | #2 | Medium |
| 25 | Model router (5-tier classification) | 2 | #24 | High |
| 26 | Prompt registry and template loading | 1 | #2 | Low |
| 27 | Tool registry and execution pipeline | 2 | #10, #14 | Medium |
| 28 | Short-term memory (conversation buffer) | 1.5 | #5 | Low |
| 29 | Long-term memory (PostgreSQL-backed) | 2 | #4, #28 | Medium |
| 30 | Semantic memory (vector search) | 2 | #4, #5 | High |
| 31 | RAG pipeline (embedding → retrieval → re-ranking) | 3 | #24, #30, #26 | High |
| 32 | LangGraph agent graph definition | 3 | #25, #27, #28, #29, #31 | High |

## Phase 6 — Integration & Operations (Week 6-7)

Dependency reasoning: Integration comes after everything is built. Testing validates the full system.

| # | Step | Effort (pd) | Prerequisites | Risk |
|---|------|-------------|---------------|------|
| 33 | n8n webhook integration (meeting, workflow triggers) | 1.5 | #21 | Medium |
| 34 | Celery worker startup and task routing | 1 | #17 | Medium |
| 35 | Saga compensation testing | 2 | #18 | High |
| 36 | Monitoring dashboards and alerting rules | 1.5 | #3, #34 | Low |
| 37 | Integration tests and E2E tests | 3 | #21, #32 | Medium |
| 38 | Deployment configuration (Docker Compose, CI/CD) | 2 | #37 | Medium |
| 39 | Security audit and penetration testing | 2 | #38 | High |
| 40 | Production readiness review | 1 | #38, #39 | Low |

## Effort Summary

| Phase | Total Effort (pd) |
|-------|-------------------|
| Phase 1 — Foundation | 6 |
| Phase 2 — Domain & Infrastructure | 9.5 |
| Phase 3 — Application Layer | 12.5 |
| Phase 4 — API & Middleware | 7.5 |
| Phase 5 — AI & Memory | 18.5 |
| Phase 6 — Integration & Operations | 11 |
| **Total** | **65 person-days (~13 weeks for a team of 5)** |

## Risk Distribution

- **High risk items:** #12, #18, #19, #21, #25, #30, #31, #32, #35, #39
- **Medium risk items:** #4, #6, #7, #8, #10, #11, #13, #14, #16, #17, #24, #27, #29, #33, #34, #37, #38
- **Low risk items:** #1, #2, #3, #5, #9, #15, #20, #22, #23, #26, #28, #36, #40

High-risk items cluster in Phase 3 (saga/command complexity), Phase 4 (auth middleware), and Phase 5 (LLM orchestration). Recommend paired programming or architectural spike for #18, #25, #31, and #32 before full implementation.

# 13. Engineering Standards

This section defines the mandatory engineering standards for all code produced in this project. Every contributor must follow these conventions. Violations are caught by automated linting, static analysis, or code review.

## 13.1 Naming Conventions

| Category | Convention | Example | Rationale |
|---|---|---|---|
| Module files (logic) | snake_case.py | conversation_repository.py | Matches Python standard library convention; import statements are readable. |
| Module files (class-only) | PascalCase.py | ConversationMapper.py | Signals that the module exports a single class; grep-friendly. |
| Classes | PascalCase | ConversationAggregate, ScheduleMeetingHandler | PEP 8 standard for class names. |
| Functions / Methods | snake_case | handle_message, get_conversation | PEP 8 standard for callables. |
| Variables | snake_case | conversation_id, user_email | PEP 8 standard for identifiers. |
| Constants | UPPER_SNAKE_CASE | MAX_RETRY_COUNT, DEFAULT_TTL | Visually distinguishes immutable values from mutable variables. |
| Private (module/class) | _prefix | _validate_state, _convert_internal | PEP 8 convention for non-public members. |
| Dunder (name mangling) | __prefix only in ORM models | __tablename__, __table_args__ | Reserved for SQLAlchemy ORM declarations to avoid collision with column names. |
| Packages | short, lowercase, single word | api, domain, tasks | PEP 8; short names avoid deep nesting and import verbosity. |
| Modules (descriptive) | snake_case | conversation_repository.py | Self-documenting file purpose. |
| Test modules | test_{module_name}.py | test_conversation_service.py | Discoverable by pytest convention. |
| Test classes | Test{ClassName} | TestConversationService | Namespace tests by class under test. |
| Test methods | test_{scenario} | test_handle_message_raises_on_empty | Verbose scenario names serve as documentation. |
| Database tables | snake_case, singular | conversation, meeting_lead | Avoids plural ambiguity; aligns with domain entity names. |
| Redis keys | colon-delimited, noun:identifier | conversation:{id}:lock | Redis namespace convention; enables key scanning by prefix. |
| Celery tasks | descriptive snake_case | process_meeting_scheduling | Task name appears in logs and monitoring dashboards. |
| Environment variables | UPPER_SNAKE_CASE with ASSISTANT_ prefix | ASSISTANT_DB_URL, ASSISTANT_REDIS_URL | Project prefix avoids collision with other services in the same environment. |

## 13.2 Package Conventions

| Rule | Specification | Rationale |
|---|---|---|
| __init__.py exports | Only public API via explicit __all__ | Prevents accidental import of internal implementation details; tooling can statically determine the public surface. |
| Internal modules | Prefixed with underscore (e.g., _helpers.py) | Signals to consumers that the module is private and subject to change without notice. |
| One class per file | Enforced except for small value objects (< 50 lines) | Simplifies navigation, git blame, and testing. |
| Maximum file length | 400 lines (split into submodules if exceeded) | Long files are difficult to review, test, and maintain. Submodules enforce separation of concerns. |
| Circular import prevention | Use TYPE_CHECKING for type hints | from __future__ import annotations combined with TYPE_CHECKING blocks avoids runtime circular imports while preserving type safety. |

Example __init__.py:

    from __future__ import annotations

    from .conversation_aggregate import ConversationAggregate
    from .events import ConversationCreated, MessageAppended
    from .value_objects import Participant, Message

    __all__ = [
        "ConversationAggregate",
        "ConversationCreated",
        "MessageAppended",
        "Participant",
        "Message",
    ]

Example TYPE_CHECKING import:

    from __future__ import annotations
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from domain.aggregates.conversation import ConversationAggregate

## 13.3 Exception Strategy

| Exception Layer | Base Exception | Concrete Exceptions | When to Use |
|---|---|---|---|
| Domain | DomainException | InvalidStateError, InvariantViolationError, BusinessRuleViolationError | Aggregate methods reject invalid state transitions, break invariants, or violate business rules. |
| Application | ApplicationException | NotFoundError, ValidationError, AuthorizationError, ConflictError | Command/query handlers encounter missing resources, invalid input, insufficient permissions, or version conflicts. |
| Infrastructure | InfrastructureException | DatabaseError, RedisError, LLMError, QueueError | External system calls fail (connection refused, timeout, rate limit). |

Exception enrichment - every exception captures context:

    class DomainException(Exception):
        def __init__(
            self,
            message: str,
            correlation_id: str | None = None,
            aggregate_id: str | None = None,
            user_id: str | None = None,
        ) -> None:
            self.correlation_id = correlation_id
            self.aggregate_id = aggregate_id
            self.user_id = user_id
            super().__init__(message)

API layer translation - ApplicationExceptions map to HTTP status codes:

| Exception | HTTP Status |
|---|---|
| NotFoundError | 404 |
| ConflictError | 409 |
| ValidationError | 422 |
| AuthorizationError | 403 |
| All others (unhandled) | 500 |

Golden rule: never catch and silently swallow. Every except block must either log-and-re-raise or handle explicitly with a compensating action.

## 13.4 Logging Strategy

| Aspect | Standard |
|---|---|
| Format | Structured JSON. Every log line is a JSON object with keys: timestamp, level, logger, message, correlation_id, service, environment. |
| Correlation ID | Propagated from HTTP request header or job trigger through all downstream calls. Attached to every log line. |
| DEBUG | Development only. Detailed diagnostic information. Never enabled in production. |
| INFO | Business events: command start/finish, aggregate creation, event publication, notification delivery. |
| WARNING | Retry attempts, degraded mode activation, cache miss rate above threshold, rate limit approaching. |
| ERROR | Operation failure after all retries exhausted, external service unreachable, invariant violation, data integrity issue. |
| CRITICAL | System component down (database unreachable, queue broker offline, LLM provider unavailable). Triggers PagerDuty alert. |
| Every command start/finish/failure | Log command_start, command_finished, command_failed with command type, aggregate ID, duration. |
| Every domain event publication | Log event_published with event type, aggregate ID, version, correlation ID. |
| Every external service call | Log external_call_start, external_call_finished, external_call_failed with service name, endpoint, duration, status code. |

PII redaction - before logging, strip or hash these patterns:

    import re

    PII_PATTERNS = {
        "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        "phone": re.compile(r"\+?1?\d{9,15}"),
        "ssn": re.compile(r"\d{3}-\d{2}-\d{4}"),
    }

    def redact_pii(message: str) -> str:
        for name, pattern in PII_PATTERNS.items():
            message = pattern.sub(f"[REDACTED:{name}]", message)
        return message

## 13.5 Dependency Injection Rules

| Rule | Detail | Rationale |
|---|---|---|
| FastAPI overrides | Use app.dependency_overrides[get_repository] = mock_repository for testing | Injects test doubles without modifying production code. |
| Constructor injection | Application services receive repositories via __init__ | Explicit dependencies; no hidden globals; testable by construction. |
| Domain service purity | Domain services receive no infrastructure dependencies | Keeps the domain layer framework-agnostic and testable without mocks. |
| Config injection | Config object injected via FastAPI dependency; never imported globally | Avoids hidden coupling to environment variables at module load time. |
| Dataclass services | Use @dataclass for service dependency declarations | Reduces boilerplate; immutable after construction; clear dependency list. |

Example:

    from dataclasses import dataclass
    from domain.repositories import ConversationRepository
    from config.settings import Settings

    @dataclass
    class ConversationService:
        conversation_repository: ConversationRepository
        settings: Settings

## 13.6 Configuration Rules

| Rule | Specification | Rationale |
|---|---|---|
| Single settings class | One Settings Pydantic model loaded from environment on startup | Single source of truth; validated at boot; provides IDE autocompletion. |
| No direct os.environ | All config access goes through the settings object | Centralised validation; testable with override fixtures. |
| Secrets via .env | .env file for local development; secrets manager (Vault / AWS Secrets Manager) for staging and production | Never hardcode secrets in source code; never commit .env to version control. |
| Feature flags | Defined in settings as bool fields; togglable at runtime via Redis override | Enables canary releases, A/B testing, and kill switches without deployment. |

    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        database_url: str
        redis_url: str
        llm_api_key: str
        feature_use_new_llm_model: bool = False

        model_config = SettingsConfigDict(env_prefix="ASSISTANT_")

    def get_settings() -> Settings:
        return Settings()

## 13.7 Repository Rules

| Rule | Specification | Rationale |
|---|---|---|
| Interface in domain | Repository interface defined in domain/repositories/ | Domain defines the contract; infrastructure provides the implementation (Hexagonal Architecture). |
| Implementation in infrastructure | Concrete repository in infrastructure/repositories/ | Infrastructure depends on domain interfaces, not the reverse. |
| Return domain aggregates | Repository methods return domain aggregates, never ORM model instances | Consumers work with domain objects; ORM details are encapsulated. |
| Single aggregate owner | Repository owns all database access for its aggregate only | Enforces aggregate consistency boundary; prevents cross-aggregate transactions. |
| Read models for queries | Complex queries bypass repositories and use read-model services | Queries do not need domain consistency; read models are optimised for presentation. |

Example interface:

    from abc import ABC, abstractmethod
    from domain.aggregates.conversation import Conversation
    from domain.value_objects.conversation_id import ConversationId

    class ConversationRepository(ABC):
        @abstractmethod
        async def save(self, conversation: Conversation) -> None: ...

        @abstractmethod
        async def load(self, conversation_id: ConversationId) -> Conversation: ...

        @abstractmethod
        async def delete(self, conversation_id: ConversationId) -> None: ...

## 13.8 DTO Rules

| Rule | Specification | Rationale |
|---|---|---|
| Request DTOs | Pydantic models with validation in api/request_models/ | Input validation at the API boundary; type-safe deserialisation. |
| Response DTOs | Pydantic models in api/response_models/ or application/dtos/ | Serialisation layer that decouples API schema from domain objects. |
| Domain-to-DTO mapping | Mappers in application/mappers/ | Separation of concerns: domain objects are not polluted with serialisation logic. |
| Never expose domain entities | API responses must never return domain entity objects | Prevents accidental leakage of internal state and creates a stable API contract independent of domain refactoring. |

Example:

    from pydantic import BaseModel
    from uuid import UUID
    from datetime import datetime

    class ConversationResponse(BaseModel):
        conversation_id: UUID
        title: str
        participant_count: int
        created_at: datetime
        last_activity_at: datetime
        status: str

## 13.9 Mapper Rules

| Rule | Specification | Rationale |
|---|---|---|
| Stateless | Mappers are stateless functions or @staticmethod classes | No mutable state; idempotent; trivially testable. |
| One per aggregate | One mapper class per aggregate root (e.g., ConversationMapper) | Clear ownership; easy to find. |
| Bidirectional mapping | Mappers handle domain -> DTO and DTO -> command | Complete translation layer. |
| No business logic | Mappers transform data only; they never validate, compute, or enforce rules | Business logic changes should never require modifying a mapper. |

Example:

    from domain.aggregates.conversation import Conversation
    from application.dtos.conversation import ConversationResponse

    class ConversationMapper:
        @staticmethod
        def to_response(conversation: Conversation) -> ConversationResponse:
            return ConversationResponse(
                conversation_id=conversation.conversation_id,
                title=conversation.title,
                participant_count=len(conversation.participants),
                created_at=conversation.created_at,
                last_activity_at=conversation.last_activity_at,
                status=conversation.status.value,
            )

## 13.10 Testing Rules

| Test Level | Scope | Dependencies | Tools | Coverage Target |
|---|---|---|---|---|
| Unit | Domain layer. Pure business logic: aggregate methods, value objects, domain services, policies, specifications. | None (all dependencies mocked via interfaces) | pytest (no DB, no network) | 90% |
| Integration | Application services, command handlers, query handlers, repository implementations | Test database (PostgreSQL test container), Redis test instance, mocked LLM | pytest + pytest-asyncio + testcontainers | 80% |
| E2E | Full flow: API endpoint -> application -> repository -> database -> response | Real database, real Redis, real LLM (staged sandbox), real n8n (staged) | pytest + httpx AsyncClient + testcontainers | 70% (critical paths only) |

Fixtures - domain object factories:

    from domain.aggregates.conversation import Conversation
    from domain.value_objects import Participant

    class ConversationFactory:
        @staticmethod
        def create(
            conversation_id: str = "test-conv-001",
            participants: list[Participant] | None = None,
        ) -> Conversation:
            return Conversation(
                conversation_id=conversation_id,
                participants=participants or [Participant(user_id="user-001")],
            )

## 13.11 Documentation Rules

| Rule | Specification | Rationale |
|---|---|---|
| README per package | Every top-level package has a README.md explaining its purpose, ownership, and key classes | New contributors onboard faster without reading every file. |
| Docstrings on public APIs | All public functions, classes, and methods have Google-style docstrings | IDEs display documentation; documentation generators (Sphinx, pydoc) produce reference docs. |
| ADRs for significant changes | Architecture Decision Records in docs/adr/ for any decision that affects cross-package structure | Provides historical context for why the system is designed the way it is. |
| Inline comments for non-obvious logic | Comments explain why, not what (the code explains what) | Reduces noise; comments that restate the code become stale. |

Example docstring:

    def handle_message(
        command: HandleMessageCommand,
    ) -> MessageResponse:
        """Process an incoming message and generate a response.

        This method orchestrates the full message processing pipeline:
        1. Validates the message and conversation state.
        2. Appends the message to the conversation aggregate.
        3. Initiates async intent classification and response generation.

        Args:
            command: The validated command containing the message content
                and conversation identifier.

        Returns:
            A response DTO containing the generated reply and metadata.

        Raises:
            ConversationNotFoundError: If the conversation does not exist.
            ParticipantNotFoundError: If the sender is not a participant.
        """

# 15. Team Responsibility Matrix

Defines ownership across 6 teams for every module, cross-cutting concern, handoff protocol, code review, and on-call rotation.

## 15.1 Module Ownership Table

| Module | Lead Team | Supporting Team(s) | Review Required By | Ownership Type | Escalation Path |
|--------|----------|-------------------|-------------------|---------------|----------------|
| api/ | Backend | Frontend, QA | Backend Lead + AI Lead | Build/Own | Backend Tech Lead -> Architect |
| api/routes/conversations | Backend | AI, Frontend | Backend Lead | Build/Own | API Lead -> Backend Tech Lead |
| api/routes/meetings | Backend | Frontend | Backend Lead | Build/Own | API Lead -> Backend Tech Lead |
| api/routes/leads | Backend | Frontend | Backend Lead | Build/Own | API Lead -> Backend Tech Lead |
| api/routes/notifications | Backend | Frontend | Backend Lead | Build/Own | API Lead -> Backend Tech Lead |
| api/routes/workflows | Backend | Platform, Frontend | Backend Lead + Platform Lead | Build/Own | API Lead -> Backend Tech Lead |
| api/routes/prompts | Backend | AI, Frontend | Backend Lead + AI Lead | Build/Own | API Lead -> Backend Tech Lead |
| api/routes/documents | Backend | AI, Frontend | Backend Lead | Build/Own | API Lead -> Backend Tech Lead |
| api/routes/analytics | Backend | QA | Backend Lead | Build/Own | API Lead -> Backend Tech Lead |
| api/routes/health | Backend | Platform, DevOps | Backend Lead + Platform Lead | Build/Own | API Lead -> Backend Tech Lead |
| api/middleware/auth | Backend | Security | Backend Lead + Security Lead | Build/Own | Security -> Backend Tech Lead |
| api/middleware/rate-limit | Backend | Platform | Backend Lead | Build/Own | API Lead -> Backend Tech Lead |
| api/middleware/identity | Backend | Security | Backend Lead + Security Lead | Build/Own | Security -> Backend Tech Lead |
| api/middleware/error-handler | Backend | QA | Backend Lead | Build/Own | API Lead -> Backend Tech Lead |
| api/middleware/request-id | Backend | Platform | Backend Lead | Build/Own | API Lead -> Backend Tech Lead |
| application/services/ | Backend | AI | Backend Lead + AI Lead | Build/Own | Application Lead -> Backend Tech Lead |
| application/handlers/commands/ | Backend | AI, QA | Backend Lead + AI Lead | Build/Own | Application Lead -> Backend Tech Lead |
| application/handlers/queries/ | Backend | QA | Backend Lead | Build/Own | Application Lead -> Backend Tech Lead |
| application/dtos/ | Backend | Frontend | Backend Lead + Frontend Lead | Build/Own | Application Lead -> Backend Tech Lead |
| application/mappers/ | Backend | None | Backend Lead | Build/Own | Application Lead -> Backend Tech Lead |
| domain/aggregates/ | Backend | AI | Backend Lead + AI Lead | Build/Own | Domain Lead -> Backend Tech Lead |
| domain/entities/ | Backend | None | Backend Lead | Build/Own | Domain Lead -> Backend Tech Lead |
| domain/value_objects/ | Backend | None | Backend Lead | Build/Own | Domain Lead -> Backend Tech Lead |
| domain/services/ | Backend | AI | Backend Lead + AI Lead | Build/Own | Domain Lead -> Backend Tech Lead |
| domain/events/ | Backend | AI, QA | Backend Lead + AI Lead | Build/Own | Domain Lead -> Backend Tech Lead |
| domain/specifications/ | Backend | None | Backend Lead | Build/Own | Domain Lead -> Backend Tech Lead |
| domain/policies/ | Backend | AI | Backend Lead + AI Lead | Build/Own | Domain Lead -> Backend Tech Lead |
| infrastructure/database/ | Backend | DevOps | Backend Lead + DevOps Lead | Build/Own | Infra Lead -> Backend Tech Lead |
| infrastructure/cache/ | Backend | DevOps | Backend Lead + DevOps Lead | Build/Own | Infra Lead -> Backend Tech Lead |
| infrastructure/queue/ | Backend | Platform | Backend Lead + Platform Lead | Build/Own | Infra Lead -> Backend Tech Lead |
| infrastructure/llm/ | AI | Backend | AI Lead + Backend Lead | Build/Own | AI Lead -> Architect |
| infrastructure/vector/ | AI | Backend, DevOps | AI Lead + DevOps Lead | Build/Own | AI Lead -> Architect |
| infrastructure/monitoring/ | Platform | Backend, DevOps | Platform Lead + DevOps Lead | Build/Own | Platform Lead -> Architect |
| repositories/ | Backend | AI, QA | Backend Lead | Build/Own | Repo Lead -> Backend Tech Lead |
| services/ (app-level) | Backend | AI | Backend Lead + AI Lead | Build/Own | Application Lead -> Backend Tech Lead |
| agents/ | AI | Backend, QA | AI Lead + Backend Lead | Build/Own | AI Lead -> Architect |
| memory/short-term/ | AI | Backend | AI Lead | Build/Own | AI Lead -> Architect |
| memory/long-term/ | Backend | AI | Backend Lead + AI Lead | Build/Own | Infra Lead -> Backend Tech Lead |
| memory/semantic/ | AI | Backend, DevOps | AI Lead + DevOps Lead | Build/Own | AI Lead -> Architect |
| rag/ | AI | Backend, DevOps | AI Lead + Backend Lead | Build/Own | AI Lead -> Architect |
| tools/ | AI | Backend | AI Lead + Backend Lead | Build/Own | AI Lead -> Architect |
| workflows/ | Platform | Backend | Platform Lead + Backend Lead | Build/Own | Platform Lead -> Architect |
| tasks/ (Celery) | Backend | Platform, DevOps | Backend Lead + Platform Lead | Build/Own | Infra Lead -> Backend Tech Lead |
| monitoring/ | Platform | DevOps | Platform Lead + DevOps Lead | Build/Own | Platform Lead -> Architect |
| config/ | Platform | All teams | Platform Lead | Build/Own | Platform Lead -> Architect |
| prompts/ | AI | Backend, QA | AI Lead + QA Lead | Build/Own | AI Lead -> Architect |
| tests/unit | QA | Backend, AI | QA Lead + Backend Lead | Build/Own | QA Lead -> Architect |
| tests/integration | QA | Backend, AI, Platform | QA Lead + Backend Lead + Platform Lead | Build/Own | QA Lead -> Architect |
| tests/e2e | QA | All teams | QA Lead + All Tech Leads | Build/Own | QA Lead -> Architect |
| tests/performance | QA | Backend, Platform | QA Lead + Platform Lead | Build/Own | QA Lead -> Architect |
| tests/security | QA | Security, Backend | QA Lead + Security Lead | Build/Own | QA Lead -> Architect |
| docker/ | Platform | DevOps | Platform Lead + DevOps Lead | Build/Own | Platform Lead -> Architect |
| ci_cd/ | Platform | DevOps, QA | Platform Lead + DevOps Lead | Build/Own | Platform Lead -> Architect |
| security/ | Platform | Backend, DevOps, QA | Platform Lead + Security Lead | Build/Own | Platform Lead -> Architect |

## 15.2 RACI Matrix for Cross-Cutting Concerns

| Concern | Backend Team | AI Team | Platform Team | DevOps Team | Frontend Team | QA Team |
|---------|-------------|---------|--------------|-------------|--------------|---------|
| Identity & Authentication | C | I | A/R | C | C | I |
| Authorization (RBAC/ABAC) | R | C | A | I | C | C |
| Observability (Logging, Metrics, Tracing) | C | I | A/R | C | I | C |
| Security (Vulnerability, Secrets, Compliance) | C | C | A/R | R | I | R |
| Configuration Management | I | I | A/R | C | I | I |
| Deployment (CI/CD Pipelines) | C | I | R | A/R | I | C |
| API Contracts & Versioning | R | C | A | I | R | C |
| Error Handling & Resilience | R | C | A | C | I | R |
| Data Retention & Privacy | C | C | A | R | I | R |
| Cost Optimization | C | I | R | A/R | I | C |
| Documentation | R | R | A | C | R | R |
| Incident Response | C | C | R | A/R | I | C |

Legend: R = Responsible (doer), A = Accountable (approver), C = Consulted (input), I = Informed (notified)

## 15.3 Team Handoff Protocol

### 15.3.1 Handoff States

`
[Build Phase] -> [Review Phase] -> [Integration Phase] -> [Test Phase] -> [Deploy Phase]
     |                 |                  |                   |               |
     v                 v                  v                   v               v
  Owning Team    Review Board        Receiving Team      QA Team        Platform/DevOps
`

### 15.3.2 Handoff Checklist

| Step | Action | Owner | Artifact | Acceptance Criteria |
|------|--------|-------|----------|-------------------|
| H1 | Complete implementation | Lead Team | PR with code, tests, docs | All lint/type checks pass, test coverage >= 85% |
| H2 | Internal review | Lead Team Senior | Reviewed PR | All comments resolved, architecture compliance verified |
| H3 | Cross-team review | Review Required By (from table 15.1) | Approval on PR | Stakeholder sign-off, API contract frozen |
| H4 | Integration branch merge | Lead Team | Merged PR | No conflicts, CI green |
| H5 | Integration test pass | QA Team | Test report | All integration tests pass in staging |
| H6 | Deployment to staging | Platform Team | Deployment log | Health checks pass, no regressions |
| H7 | Performance validation | QA Team | Benchmark report | Latency P99 < SLA, throughput meets targets |
| H8 | Security scan | Platform/QA Team | Scan report | No critical/high vulnerabilities |
| H9 | Production deployment approval | Platform Lead | Change request | All H1-H8 artifacts approved |
| H10 | Production rollout | DevOps Team | Rollout log | Canary stable, metrics nominal, no alerts |

### 15.3.3 Handoff Escalation

| Blocking Issue | Resolution Path | Time to Escalate |
|---------------|----------------|-----------------|
| Architecture disagreement | Lead Team -> Architect -> Architecture Review Board | 24h |
| Integration conflict | Receiving Team + Lead Team -> Backend Tech Lead | 4h |
| Test failure | Lead Team + QA Team -> QA Lead | 8h |
| Performance regression | Lead Team + QA Team -> Architect | 24h |
| Security vulnerability | Lead Team + Platform Team -> Security Lead | Immediate |
| Production incident | DevOps Team -> On-call -> Incident Commander | Immediate |

### 15.3.4 Knowledge Transfer Requirements

| Artifact | Required Before Handoff | Owner |
|----------|------------------------|-------|
| Architecture Decision Record (ADR) | H3 | Lead Team |
| API documentation (OpenAPI) | H3 | Lead Team |
| Runbook (operational procedures) | H5 | Lead Team + Platform |
| Monitoring dashboard link | H6 | Lead Team + Platform |
| Alert threshold definitions | H6 | Lead Team + Platform |
| Database migration scripts | H4 | Lead Team |
| Configuration templates | H4 | Lead Team |
| Test data fixtures | H5 | Lead Team |
| Performance baseline report | H7 | Lead Team |

## 15.4 Code Review Ownership

### 15.4.1 Review Requirements by Module

| Module Area | Primary Reviewer(s) | Secondary Reviewer(s) | Must Approve Before Merge |
|------------|-------------------|----------------------|---------------------------|
| domain/ | Backend Domain Lead | AI Lead (if domain touches agent) | Backend Tech Lead |
| application/ | Backend Application Lead | QA Lead (for testability) | Backend Tech Lead |
| api/routes/ | Backend API Lead | Frontend Lead (contract impact) | Backend Tech Lead |
| api/middleware/ | Backend Tech Lead | Security Lead (auth middleware) | Backend Tech Lead |
| infrastructure/database/ | Backend Infra Lead | DevOps Lead (perf impact) | Backend Tech Lead |
| infrastructure/cache/ | Backend Infra Lead | DevOps Lead | Backend Tech Lead |
| infrastructure/llm/ | AI Lead | Backend Tech Lead | Architect |
| infrastructure/vector/ | AI Lead | DevOps Lead | AI Lead |
| infrastructure/monitoring/ | Platform Lead | DevOps Lead | Platform Lead |
| infrastructure/queue/ | Backend Infra Lead | Platform Lead | Backend Tech Lead |
| repositories/ | Backend Infra Lead | AI Lead (if agent-facing) | Backend Tech Lead |
| agents/ | AI Lead | Backend Tech Lead | Architect |
| memory/ | AI Lead | Backend Infra Lead | AI Lead |
| rag/ | AI Lead | Backend Tech Lead | Architect |
| tools/ | AI Lead | Backend Tech Lead | AI Lead |
| workflows/ | Platform Lead | Backend Tech Lead | Platform Lead |
| tasks/ (Celery) | Backend Infra Lead | Platform Lead | Backend Tech Lead |
| monitoring/ (dir) | Platform Lead | DevOps Lead | Platform Lead |
| config/ | Platform Lead | All Tech Leads | Platform Lead |
| prompts/ | AI Lead | QA Lead | AI Lead |
| tests/ | QA Lead | Relevant Team Lead | QA Lead |
| docker/ | Platform Lead | DevOps Lead | Platform Lead |
| ci_cd/ | Platform Lead | DevOps Lead | Platform Lead |
| security/ | Platform Lead + Security Lead | All Tech Leads | Architect |

### 15.4.2 Review Depth Requirements

| Change Type | Review Level | Required Reviewers | Max Review Time |
|------------|-------------|-------------------|----------------|
| Bug fix (trivial, 1-10 lines) | Light | 1 primary reviewer | 4h |
| Bug fix (complex, 11-50 lines) | Standard | 1 primary + 1 secondary | 8h |
| New feature (new module) | Deep | 2 primary + 1 secondary + tech lead | 24h |
| Refactor (no behavior change) | Standard | 1 primary | 8h |
| Configuration change | Light | 1 platform reviewer | 2h |
| Database migration | Deep | Backend Infra Lead + DevOps Lead | 8h |
| API contract change | Deep | Backend Lead + Frontend Lead + QA Lead | 16h |
| Dependency upgrade | Standard | 1 primary + security scan | 8h |
| Security fix | Deep | Security Lead + Tech Lead | 4h (emergency) |

### 15.4.3 Review Responsibility by Team

| Team | Primary Review Area | Cross-Team Review Responsibility |
|------|-------------------|--------------------------------|
| Backend Team | domain/, application/, api/, infrastructure/database/, infrastructure/cache/, infrastructure/queue/, repositories/, services/, tasks/ | Review AI team's infrastructure/llm/ and infrastructure/vector/ for integration correctness |
| AI Team | agents/, memory/, rag/, tools/, prompts/, infrastructure/llm/, infrastructure/vector/ | Review Backend team's application/ handlers that invoke AI services |
| Platform Team | config/, monitoring/, ci_cd/, docker/, security/, workflows/ | Review all teams' docker/, config/ changes for standards compliance |
| DevOps Team | ci_cd/, docker/, infrastructure/ (deployment config) | Review Platform team's security/ and monitoring/ for operational readiness |
| Frontend Team | API contracts (spec review only) | Review all API route changes for backward compatibility |
| QA Team | tests/ | Review all production code for testability, review test coverage gaps |

## 15.5 On-Call Rotation Ownership Per Module

### 15.5.1 Primary On-Call by Module

| Module | Tier | Primary On-Call | Secondary On-Call | Escalation | SLA (Response) |
|--------|------|-----------------|-------------------|-----------|---------------|
| api/routes/ (all) | 1 | Backend Team | Platform Team | Backend Tech Lead | 5min (P0), 15min (P1) |
| api/middleware/auth | 1 | Backend Team | Security Lead | Security Lead | 5min (P0) |
| api/middleware/rate-limit | 2 | Backend Team | Platform Team | Backend Tech Lead | 15min (P1) |
| application/services/ | 1 | Backend Team | AI Team | Backend Tech Lead | 5min (P0), 15min (P1) |
| application/handlers/ | 1 | Backend Team | AI Team | Backend Tech Lead | 5min (P0), 15min (P1) |
| domain/ (all) | 2 | Backend Team | AI Team | Backend Tech Lead | 30min (P2) |
| infrastructure/database/ | 1 | Backend Team | DevOps Team | Backend Tech Lead | 5min (P0) |
| infrastructure/cache/ | 1 | Backend Team | DevOps Team | Backend Tech Lead | 5min (P0) |
| infrastructure/queue/ | 1 | Backend Team | Platform Team | Backend Tech Lead | 5min (P0) |
| infrastructure/llm/ | 1 | AI Team | Backend Team | AI Lead | 5min (P0) |
| infrastructure/vector/ | 2 | AI Team | DevOps Team | AI Lead | 15min (P1) |
| infrastructure/monitoring/ | 2 | Platform Team | DevOps Team | Platform Lead | 15min (P1) |
| repositories/ | 2 | Backend Team | AI Team | Backend Tech Lead | 15min (P1) |
| agents/ | 1 | AI Team | Backend Team | AI Lead | 5min (P0) |
| memory/ | 2 | AI Team | Backend Team | AI Lead | 15min (P1) |
| rag/ | 1 | AI Team | Backend Team | AI Lead | 5min (P0) |
| tools/ | 2 | AI Team | Backend Team | AI Lead | 15min (P1) |
| workflows/ | 2 | Platform Team | Backend Team | Platform Lead | 15min (P1) |
| tasks/ (Celery) | 1 | Backend Team | Platform Team | Backend Tech Lead | 5min (P0) |
| monitoring/ (dir) | 2 | Platform Team | DevOps Team | Platform Lead | 15min (P1) |
| config/ | 2 | Platform Team | All Teams | Platform Lead | 15min (P1) |
| prompts/ | 2 | AI Team | QA Team | AI Lead | 30min (P2) |
| ci_cd/ | 2 | Platform Team | DevOps Team | Platform Lead | 15min (P1) |
| docker/ | 2 | Platform Team | DevOps Team | Platform Lead | 15min (P2) |
| security/ | 1 | Platform Team | DevOps Team, Security Lead | Platform Lead | 5min (P0) |

### 15.5.2 Severity Level Definitions

| Severity | Definition | Response SLA | Resolution SLA | Communication |
|----------|-----------|-------------|---------------|--------------|
| P0 (Critical) | Complete service outage, data loss, security breach | 5min | 1h | Public status page + all-hands Slack |
| P1 (High) | Major feature degradation, partial outage, >10% error rate | 15min | 4h | Team Slack + weekly report |
| P2 (Medium) | Minor feature impairment, <5% error rate, single user issue | 30min | 24h | Ticket update |
| P3 (Low) | Cosmetic issue, documentation, enhancement request | 1h | 7 days | Ticket update |

### 15.5.3 On-Call Rotation Schedule

| Team | Rotation Size | Shift Duration | Handoff Time | Overlap Period |
|------|--------------|---------------|-------------|---------------|
| Backend Team | 6 (weekly rotation) | 7 days | Mon 09:00 UTC | 30min handoff |
| AI Team | 4 (weekly rotation) | 7 days | Mon 09:00 UTC | 30min handoff |
| Platform Team | 3 (weekly rotation) | 7 days | Mon 09:00 UTC | 30min handoff |
| DevOps Team | 3 (weekly rotation) | 7 days | Mon 09:00 UTC | 30min handoff |
| QA Team | Business hours only | N/A | N/A | N/A (P0 escalates to engineering team) |

### 15.5.4 Handoff Protocol for On-Call

`
1. Outgoing on-call prepares handoff document:
   - Active incidents (status, timeline, next steps)
   - PagerDuty alert history summary
   - Known issues and workarounds
   - Maintenance windows planned for the week
   - Links to relevant runbooks

2. Overlap call (30min):
   - Walk through each active incident
   - Demo any new monitoring dashboards or alerts
   - Transfer PagerDuty escalation policy
   - Transfer Slack / OpsGenie ownership

3. Outgoing on-call stays available for 2h after handoff for questions

4. Handoff doc is posted to #ops-oncall Slack channel
`

### 15.5.5 Escalation Paths

| If On-Call is Unreachable | Escalate To | After |
|--------------------------|-------------|-------|
| Backend Team | Backend Tech Lead | 5min (P0), 15min (P1) |
| AI Team | AI Lead | 5min (P0), 15min (P1) |
| Platform Team | Platform Lead | 5min (P0), 15min (P1) |
| DevOps Team | DevOps Lead | 5min (P0), 15min (P1) |
| Any Tech Lead | Architect | 10min (P0), 30min (P1) |
| Architect | CTO / VP Engineering | 15min (P0) |


# 16. Risk Before Coding

Identifies all hidden risks across the architecture that must be addressed before any code is written. Each risk includes detection method, mitigation strategy, and ownership. Risk Score = Likelihood × Impact (each rated 1-5).

## 16.1 Hidden Coupling

| Risk ID | Category | Description | Likelihood (1-5) | Impact (1-5) | Risk Score | Detection | Mitigation | Owner |
|---------|----------|-------------|------------------|--------------|------------|-----------|------------|-------|
| R1 | Hidden Coupling | Conversation aggregate couples to Memory, Lead, Workflow through event handlers — implicit dependency graph obscure aggregate boundaries | 3 | 3 | 9 | Static analysis of event handler imports; architecture test enforcing that handlers only reference their owning aggregate | Define explicit event contracts per aggregate; enforce that event handlers live in the consuming aggregate's package; use ArchUnit-style tests to verify no cross-aggregate direct references | Backend Team |
| R2 | Hidden Coupling | HandleMessage command spans 4 aggregates (Conversation, Memory, User, Workflow) — transactional boundary is unclear, partial failures risk inconsistent state | 4 | 4 | 16 | Code review of HandleMessage handler; transaction scope analysis tool | Restructure HandleMessage as a saga with compensating actions per aggregate; each aggregate operation commits independently with its own unit of work; never share a DB transaction across aggregates | Backend Team |
| R3 | Hidden Coupling | Memory confirmation policy couples to LLM confidence scoring — if LLM confidence calibration changes, memory confirmation logic silently breaks | 3 | 3 | 9 | Integration test that varies LLM confidence thresholds and verifies memory confirmation behavior | Extract confidence scoring behind a domain service interface with versioned implementation; add explicit confidence threshold configuration in domain policies; write property-based tests over the full confidence range | AI Team |

## 16.2 Circular Dependencies

| Risk ID | Category | Description | Likelihood (1-5) | Impact (1-5) | Risk Score | Detection | Mitigation | Owner |
|---------|----------|-------------|------------------|--------------|------------|-----------|------------|-------|
| R4 | Circular Dependencies | Conversation → Memory → Embedding → Knowledge → Conversation — potential circular reference through event chain at runtime | 3 | 4 | 12 | Dependency graph visualization tool; runtime event trace with circular reference detection; ArchUnit cycle check across all packages | Enforce strict event flow direction: Conversation emits → Memory consumes; Memory emits → Knowledge consumes; Knowledge never emits events back to Conversation; use a Mediator/Observer bus that logs and blocks cycles in dev mode | Backend Team |
| R5 | Circular Dependencies | Event handlers may import each other (e.g., MemoryUpdated triggers WorkflowExecution, which triggers Notification, which triggers Memory update) | 3 | 3 | 9 | Import cycle detection in CI pipeline; runtime event cascade depth limit with alert | Implement event cascade depth limit (max 3 hops) with dead-letter after limit; add a circuit breaker per event type that suppresses re-triggering within a configurable cooldown window; enforce acyclic event flow in architecture tests | Platform Team |

## 16.3 Package Violations

| Risk ID | Category | Description | Likelihood (1-5) | Impact (1-5) | Risk Score | Detection | Mitigation | Owner |
|---------|----------|-------------|------------------|--------------|------------|-----------|------------|-------|
| R6 | Package Violations | Repository implementations importing domain value objects directly instead of through repository interfaces — bypasses abstraction layer | 4 | 3 | 12 | Automated dependency rule check in CI (e.g., ArchUnit, import-linter); code review checklist item for repository classes | Enforce that repositories/ package may only import domain/ interfaces, not domain/ entities or value objects; add linter rule banning domain/.* imports in repositories/ except domain/interfaces/ | Backend Team |
| R7 | Package Violations | API DTOs being used in application layer instead of domain types — couples API shape to internal logic and prevents domain purity | 3 | 2 | 6 | Static analysis import check; code review flag when application/ references api/ | Enforce strict dependency rule: api/ → application/ → domain/ (never the reverse); add CI check using dependency-cruiser or similar tool; use mapper layer to convert between DTO and domain types | Backend Team |

## 16.4 Repository Leaks

| Risk ID | Category | Description | Likelihood (1-5) | Impact (1-5) | Risk Score | Detection | Mitigation | Owner |
|---------|----------|-------------|------------------|--------------|------------|-----------|------------|-------|
| R8 | Repository Leaks | Repository methods returning ORM models instead of domain aggregates — leaks infrastructure dependency into application layer | 4 | 4 | 16 | Code inspection of all repository method return types; integration test asserting return type is domain aggregate, not ORM model | Repository interface must declare domain aggregate return types only; add a custom pylint/mypy rule that flags ORM model imports in repositories/ package; enforce in code review | Backend Team |
| R9 | Repository Leaks | Query logic bleeding into repository instead of staying in query handlers — repository becomes a god class with filtered/find methods | 4 | 3 | 12 | Count repository methods vs query handler methods; flag repositories exceeding N methods (threshold: 10) | Query handlers own all read logic; repository interface exposes only find_by_id and save/delete; complex queries use specification pattern or dedicated read-model repositories; enforce method count limit in CI | Backend Team |

## 16.5 Business Logic Leaks

| Risk ID | Category | Description | Likelihood (1-5) | Impact (1-5) | Risk Score | Detection | Mitigation | Owner |
|---------|----------|-------------|------------------|--------------|------------|-----------|------------|-------|
| R10 | Business Logic Leaks | Validation logic in API layer instead of domain — allows inconsistent validation across different entry points (API, events, Celery) | 3 | 3 | 9 | Review all API validators; check if domain invariants are duplicated outside domain | Domain aggregate validates all invariants in constructor/factory methods; API layer validates only transport concerns (format, required fields, type coercion); domain validation is always invoked before any state mutation | Backend Team |
| R11 | Business Logic Leaks | State transition logic in application services instead of domain state machines — state machine rules scattered across services, leading to inconsistent transitions | 3 | 3 | 9 | Code search for state transition logic outside domain/aggregates; audit all state-changing methods in application/services/ | Define explicit state machine in domain aggregate with valid_transitions method; application services call aggregate.transition(new_state) which internally validates and applies; all state changes go through the aggregate root | Backend Team |

## 16.6 Infrastructure Leakage

| Risk ID | Category | Description | Likelihood (1-5) | Impact (1-5) | Risk Score | Detection | Mitigation | Owner |
|---------|----------|-------------|------------------|--------------|------------|-----------|------------|-------|
| R12 | Infrastructure Leakage | Celery task definitions knowing domain event structures — changing a domain event field breaks serialization in tasks layer silently | 4 | 3 | 12 | Schema validation test that generates tasks payload from domain event schema and checks compatibility; Pydantic model drift detection | Tasks layer receives serialized event payloads through a well-defined event envelope (event_type, version, payload); domain events use versioned schemas; Celery tasks deserialize through a versioned event registry that supports schema migration | Backend Team |
| R13 | Infrastructure Leakage | Direct Redis/LiteLLM usage in application services instead of through repository/service abstraction — hard-codes infrastructure dependency and prevents testing | 4 | 4 | 16 | Static analysis flagging redis/ or litellm imports outside infrastructure/ package; code review checklist item | All Redis access goes through cache repository interfaces (domain layer); all LLM calls go through LlmService interface (infrastructure); application services inject interfaces, never concrete clients; enforce via import linter | Backend Team |

## 16.7 Shared State Risks

| Risk ID | Category | Description | Likelihood (1-5) | Impact (1-5) | Risk Score | Detection | Mitigation | Owner |
|---------|----------|-------------|------------------|--------------|------------|-----------|------------|-------|
| R14 | Shared State Risks | Conversation state in Redis + PostgreSQL dual write — if Redis write succeeds but PostgreSQL write fails (or vice versa), state diverges with no reconciliation mechanism | 4 | 4 | 16 | Chaos engineering test that simulates partial write failure; monitoring alert on cache-vs-db key divergence | Make PostgreSQL the source of truth; Redis is a read-only cache populated after DB write succeeds; implement periodic reconciliation job that syncs Redis from DB with drift detection and alerting; use CDC (change data capture) for near-real-time cache invalidation | Backend Team |
| R15 | Shared State Risks | Session identity cache (Redis) vs database — stale identity risk when user profile is updated but Redis session cache retains old roles/permissions | 3 | 3 | 9 | Integration test that updates user profile and checks session cache TTL behavior; monitoring on session cache staleness | Use short TTL on session cache (5 minutes max) with lazy invalidation on profile update; implement a session version field that increments on profile changes; Redis key includes version so outdated entries are automatically rejected; add webhook to actively evict session on profile change | Backend Team |

## 16.8 Concurrency Risks

| Risk ID | Category | Description | Likelihood (1-5) | Impact (1-5) | Risk Score | Detection | Mitigation | Owner |
|---------|----------|-------------|------------------|--------------|------------|-----------|------------|-------|
| R16 | Concurrency Risks | Same user sending two messages simultaneously — conversation lock race can cause message ordering inversion, duplicate messages, or lost updates | 4 | 5 | 20 | Load test with concurrent message sends from same conversation; verify message order and count invariants | Implement Redis distributed lock on conversation:{id}:lock for message append operations; use optimistic concurrency (version field on Conversation aggregate); reject concurrent writes with 409 Conflict and retry-after header; client-side dedup with idempotency key | Backend Team |
| R17 | Concurrency Risks | Meeting availability double-booking — slot reservation race when two users book the same time slot simultaneously | 4 | 5 | 20 | Load test with concurrent booking requests for the same slot; verify no overlapping bookings | Use Redis transaction (MULTI/EXEC with WATCH on slot bitmap) for atomic slot reservation; implement two-phase booking: temporary lock (2min TTL) then confirm with DB transaction; reject stale locks older than 2min; add database-level unique constraint on (start_time, participant_id) | Backend Team |

## 16.9 Scaling Risks

| Risk ID | Category | Description | Likelihood (1-5) | Impact (1-5) | Risk Score | Detection | Mitigation | Owner |
|---------|----------|-------------|------------------|--------------|------------|-----------|------------|-------|
| R18 | Scaling Risks | LLM rate limiting under high concurrency — 5-tier router may still exhaust high-tier credits during traffic spikes, causing cascading fallthrough and degraded responses | 3 | 4 | 12 | Load test at 2x expected peak concurrency; monitor tier credit consumption rate; chaos test by simulating tier exhaustion | Implement adaptive rate limiter per tier with dynamic backoff; add a circuit breaker that pauses low-priority requests when high-tier credits approach limit; pre-allocate credits per tenant with burst allowance; queue overflow requests with bounded delay; alert when credit consumption exceeds 80% of rate limit | AI Team |
| R19 | Scaling Risks | Embedding generation queue backpressure — if embedding consumer (Celery worker) cannot keep up with producer (message ingestion), queue grows unbounded and embedding staleness increases | 3 | 3 | 9 | Monitor Celery queue depth for embedding tasks; alert on queue growth trend; track embedding staleness metric (time since last embedding) | Implement dynamic concurrency scaling for embedding workers (Celery autoscaling based on queue depth); add priority queue where real-time messages get higher priority than batch reindexing; use embedding batching (process N messages per worker invocation) for throughput; implement queue TTL with skip-and-log for messages older than 1 hour | AI Team |
| R20 | Scaling Risks | Redis memory exhaustion with conversation history cache — caching last 50 messages per conversation across thousands of concurrent conversations can exceed Redis memory limits | 3 | 3 | 9 | Monitor Redis memory usage with Grafana; set alert at 75% maxmemory; simulate peak concurrent conversations in load test | Set maxmemory-policy allkeys-lru on Redis so least-recently-used conversation caches evict first; reduce per-conversation cache cap from 50 to 20 messages for tenant tiers below enterprise; implement Redis key TTL based on conversation activity (shorter TTL for idle conversations); add conversation summary cache that replaces full message cache for very old conversations | DevOps Team |


# 17. Coding Readiness Checklist

This section defines the exhaustive checklist that must be completed and verified before Phase 4 (Implementation) begins. Every item must be signed off as "Approved" before the team proceeds to coding. Status values: Pending, In Review, Approved, Blocked.

---

## 17.1 Architecture & Design (Gate Check)

| Section | Item | Acceptance Criteria | Evidence | Responsible | Status |
|---------|------|-------------------|----------|-------------|--------|
| 17.1 | Architecture approved by all stakeholders | Signed ARCHITECTURE.md v1.0 with all stakeholder signatures | Signed PDF containing ARCHITECTURE.md v1.0 with sign-off from all principal architects | Lead Architect + Architecture Review Board | Pending |
| 17.1 | DDD approved by domain experts | Signed DOMAIN_MODEL.md v1.0 with domain expert signatures | Signed PDF containing DOMAIN_MODEL.md v1.0 with domain expert sign-off on all 9 aggregates | Domain Lead + Domain Experts | Pending |
| 17.1 | Implementation Blueprint approved | Signed IMPLEMENTATION_BLUEPRINT.md v1.0 | Signed PDF containing IMPLEMENTATION_BLUEPRINT.md v1.0 | Lead Architect | Pending |
| 17.1 | All 8 ADRs (001-008) approved and closed | All ADR items resolved, no open objections | ADR status dashboard showing all 8 ADRs as Approved/Closed | Architecture Review Board | Pending |
| 17.1 | All 8 extension ADRs (101-108) approved and closed | All extension ADR items resolved, no open objections | ADR status dashboard showing all 8 extension ADRs as Approved/Closed | Architecture Review Board | Pending |
| 17.1 | Architecture readiness score >= 9.0/10 (current: 9.2) | Self-assessment score >= 9.0 verified by peer review | Signed readiness assessment with per-criterion scores, total = 9.2 | Lead Architect | Pending |
| 17.1 | Domain model readiness score >= 9.0/10 (current: 9.3) | Self-assessment score >= 9.0 verified by domain expert review | Signed readiness assessment with per-criterion scores, total = 9.3 | Domain Lead | Pending |
| 17.1 | Implementation blueprint readiness score >= 9.8/10 | Self-assessment score >= 9.8 verified by peer review | Signed readiness assessment with per-criterion scores | Lead Architect | Pending |

## 17.2 Repository Design

| Section | Item | Acceptance Criteria | Evidence | Responsible | Status |
|---------|------|-------------------|----------|-------------|--------|
| 17.2 | All 7 repository interfaces defined in domain layer | 7 interface classes exist in domain/repositories/ with full method signatures and type annotations | Source tree listing showing 7 interface files; mypy strict passes on domain/repositories/ | Backend Team | Pending |
| 17.2 | All repository implementations planned with SQLAlchemy stubs | Stub implementation files exist in infrastructure/repositories/ with class headers, method signatures, and placeholder implementations | Source tree listing showing 7 stub files; CI lint passes | Backend Team | Pending |
| 17.2 | All repository methods documented with input/output types | Every repository method has complete type annotations and Google-style docstrings | mypy --strict passes on repositories/; docstring coverage report = 100% | Backend Team | Pending |
| 17.2 | Read models defined for all query handlers | Read model DTO classes exist in application/dtos/ for each of the 27 queries | Source tree listing showing 27 read model DTO files mapped to query handlers in section 5.1 | Backend Team | Pending |

## 17.3 API Design

| Section | Item | Acceptance Criteria | Evidence | Responsible | Status |
|---------|------|-------------------|----------|-------------|--------|
| 17.3 | All endpoints defined with request/response schemas | Pydantic request and response models exist for every endpoint in section 7 | Source tree listing matching endpoints in section 7; OpenAPI schema generation confirms all 40+ endpoints | Backend Team | Pending |
| 17.3 | All middleware components scoped and specified | 5 middleware classes exist (identity, auth, rate-limit, request-id, error-handler) with interface definitions | Source tree listing showing middleware files; each has documented purpose and ordering | Backend Team | Pending |
| 17.3 | Error response format standardized (RFC 7807 problem details) | All error responses use RFC 7807 application/problem+json format with type, title, status, detail, instance fields | Integration test verifying error response shape for 4xx and 5xx responses | Backend Team | Pending |
| 17.3 | API versioning strategy finalized (URL prefix: /api/v1) | All routes registered under /api/v1/ prefix; no unversioned routes exist | Route listing showing all endpoints under /api/v1/; deprecation policy documented in ADR | Backend Team | Pending |

## 17.4 Redis Design

| Section | Item | Acceptance Criteria | Evidence | Responsible | Status |
|---------|------|-------------------|----------|-------------|--------|
| 17.4 | All Redis key patterns defined (21 keys across 9 categories) | All 21 key patterns from section 9.11 TTL summary table implemented in infrastructure/cache/ with documented patterns | Key pattern registry showing all 21 keys with namespace, pattern, and data type | Backend Infra Team | Pending |
| 17.4 | TTL policies documented for every key | Every key pattern has a documented TTL value, extension policy, and rationale | TTL policy table (section 9.11) is complete and verified against implementation | Backend Infra Team | Pending |
| 17.4 | Eviction strategy per data type | Each key pattern specifies eviction strategy (volatile-lru, allkeys-lru, volatile-ttl, no-eviction) in its design doc | Eviction strategy column in each key's specification table (section 9.2-9.10) filled and consistent with Redis config | Backend Infra Team | Pending |
| 17.4 | Sentinel failover test plan written | Test plan covering master failure, replica promotion, quorum loss, and auto-recovery scenarios | Test plan document reviewed and approved by DevOps; test run in staging with results | DevOps Team | Pending |
| 17.4 | Degradation mode stubs defined (3 tiers) | Tier 1 (Redis down): fallback to DB; Tier 2 (high latency): local cache; Tier 3 (partial outage): graceful feature degradation | Degradation mode document with per-key failover behavior (from section 9); stubs in infrastructure/cache/degradation.py | Backend Infra Team | Pending |

## 17.5 Celery Design

| Section | Item | Acceptance Criteria | Evidence | Responsible | Status |
|---------|------|-------------------|----------|-------------|--------|
| 17.5 | All 8 worker queues defined with priority | 8 queue definitions in Celery config matching section 8.1, each with priority, concurrency, and timeout settings | Celery config file showing all 8 queues with task routing; worker startup logs verify queue registration | Backend Infra Team | Pending |
| 17.5 | Retry policies documented per queue | Each queue has documented retry strategy (exponential backoff, max retries, jitter) mapped to its tasks | Retry policy table (section 6.4) complete; Celery task annotations match declared policy | Backend Infra Team | Pending |
| 17.5 | Dead letter queue strategy finalized | DLQ architecture (section 6.5-6.6) implemented with TTLs, replay mechanisms, and monitoring per queue | DLQ queues exist in Celery config; replay tasks defined; DLQ monitoring dashboard configured | Backend Infra Team | Pending |
| 17.5 | Worker concurrency settings configured | Concurrency values from section 8.1 applied to worker startup commands; autoscaling thresholds documented | Worker deployment config (Docker Compose, K8s manifests) shows correct concurrency params | Platform Team | Pending |

## 17.6 Prompt Registry

| Section | Item | Acceptance Criteria | Evidence | Responsible | Status |
|---------|------|-------------------|----------|-------------|--------|
| 17.6 | File-based prompt directory structure created | Directory tree prompts/{category}/{prompt_name}/v{version}/ exists with at least one template file | Source tree listing showing prompt directory structure; prompts/ folder committed to repo | AI Team | Pending |
| 17.6 | Version naming convention documented | Convention doc (e.g., v{major}.{minor}+{build}) with rules for bumping, backporting, and deprecation | ADR or README in prompts/ specifying version naming convention with examples | AI Team | Pending |
| 17.6 | Active prompt selection algorithm finalized | Algorithm for resolving active prompt version (exact version, latest, environment-tagged, A/B test) documented and stubbed | Algorithm spec approved; stub function get_active_prompt(prompt_id, context) exists in prompts/registry.py | AI Team | Pending |
| 17.6 | Rollback mechanism defined | Rollback procedure (manual promote of previous version, automated on error threshold breach) documented and approved | Rollback playbook documented; rollback_prompt() stub exists in prompts/registry.py | AI Team | Pending |

## 17.7 Security

| Section | Item | Acceptance Criteria | Evidence | Responsible | Status |
|---------|------|-------------------|----------|-------------|--------|
| 17.7 | Identity resolution (3-tier) final architecture approved | Tier 1 (session token), Tier 2 (API key), Tier 3 (anonymous + JWT) with documented fallback chain | Architecture diagram showing 3-tier resolution flow; ADR documenting tier decision criteria | Security Lead + Backend Team | Pending |
| 17.7 | Authentication middleware specification complete | Auth middleware spec covering token validation, session refresh, anonymous identity creation, and public endpoint bypass | Auth middleware interface in api/middleware/auth.py with full docstrings; test plan for each auth flow | Backend Team | Pending |
| 17.7 | Authorization (RBAC) model documented | Role hierarchy, permission matrix per endpoint (section 7), and resource-level access control document | RBAC document listing roles (admin, manager, agent, user), permissions per role, and enforcement points | Security Lead | Pending |
| 17.7 | Rate limiting strategy finalized | Per-user, per-IP, per-tenant rate limits with sliding window algorithm, burst allowance, and exceeded-action (section 8.4) | Rate limit config in settings; rate limit middleware stub; per-endpoint limits from section 7 verified | Backend Team | Pending |
| 17.7 | PII redaction rules documented | PII pattern list (section 13.4) with redaction strategy (hash, mask, drop) per data type and context | PII redaction policy document; redact_pii() function exists in config/pii.py or similar | Security Lead + Platform Team | Pending |
| 17.7 | Secrets management strategy approved | Strategy for local (.env), staging (env vars), production (Vault/AWS Secrets Manager) with rotation policy and access audit | ADR documenting secrets management; integration test verifying secret loading from each environment | Security Lead + Platform Team | Pending |

## 17.8 Monitoring

| Section | Item | Acceptance Criteria | Evidence | Responsible | Status |
|---------|------|-------------------|----------|-------------|--------|
| 17.8 | Health check endpoints defined (liveness, readiness, dependency-specific) | /health/live, /health/ready, /health/db, /health/redis, /health/llm endpoints exist with correct status logic | Source code for health check endpoints; GET /health/* returns correct 200/503 responses | Platform Team | Pending |
| 17.8 | Metric dashboards specified | Grafana dashboard JSON for at least: request rate/latency/errors, queue depth, worker health, Redis hit rate, DB connection pool | Dashboard JSON reviewed and imported to staging Grafana; screenshot attached to readiness doc | Platform Team | Pending |
| 17.8 | Alerting rules defined per severity | PagerDuty alert rules for: P0 (service down, data loss), P1 (high error rate, high latency), P2 (queue backpressure, cache miss spike) | Alert rule definitions in monitoring/alerts/ with thresholds, aggregation windows, and notification channels | Platform Team | Pending |
| 17.8 | Structured logging format agreed | JSON log schema with required fields (timestamp, level, logger, message, correlation_id, service, environment) approved | Log schema document; structured logging configuration in config/ verified by integration test | Platform Team + Backend Team | Pending |
| 17.8 | Distributed tracing plan (LangSmith) confirmed | LangSmith integration scoped: trace propagation from API through Celery to LLM calls; sampling rate decided | LangSmith configuration in settings; trace capture verified for HandleMessage command flow | AI Team + Platform Team | Pending |

## 17.9 Configuration

| Section | Item | Acceptance Criteria | Evidence | Responsible | Status |
|---------|------|-------------------|----------|-------------|--------|
| 17.9 | Settings class finalized with all env vars | Pydantic Settings class with all env vars prefixed with ASSISTANT_, with validation and default values | config/settings.py imported without error; ASSISTANT_* env vars documented in .env.example | Platform Team | Pending |
| 17.9 | Feature flag mechanism implemented | Feature flag system (Redis-backed overrides with Pydantic defaults) with toggle API and TTL | Feature flag service in config/feature_flags.py; GET /config endpoint returns flags; flag override API works | Platform Team | Pending |
| 17.9 | Environment-specific config files scoped | .env.dev, .env.staging, .env.prod templates with environment-appropriate defaults and secrets placeholders | Config template files exist; no hardcoded secrets; CI loads correct env file per stage | Platform Team | Pending |

## 17.10 Testing Strategy

| Section | Item | Acceptance Criteria | Evidence | Responsible | Status |
|---------|------|-------------------|----------|-------------|--------|
| 17.10 | Unit test framework and conventions agreed | pytest with pytest-asyncio selected; test file naming test_*.py; test class naming Test*; fixture pattern agreed | Conventions doc in tests/CONTRIBUTING.md; sample unit test for domain aggregate merged to main | QA Team | Pending |
| 17.10 | Integration test environment defined | Testcontainers (PostgreSQL, Redis) or Docker Compose for CI integration tests; mocked LLM provider | docker-compose.test.yml or testcontainers config; CI job spins up dependencies before test run | QA Team + Platform Team | Pending |
| 17.10 | E2E test scenarios prioritized | Top 10 E2E scenarios identified by business criticality (create conversation, send message, schedule meeting, qualify lead, etc.) | Prioritized E2E test scenario list reviewed by Product Owner and approved | QA Team + Product Owner | Pending |
| 17.10 | Test data factories designed | Factory classes or factory-boy fixtures exist for all 9 aggregates with sensible defaults | Factory code in tests/factories/; ConversationFactory, MeetingFactory, etc. produce valid domain objects | QA Team + Backend Team | Pending |
| 17.10 | Coverage targets agreed (90/80/70) | Unit coverage >= 90%, integration coverage >= 80%, E2E critical path coverage >= 70% | Coverage config in pyproject.toml; CI gate enforces minimum thresholds per test level | QA Team | Pending |

## 17.11 Development Environment

| Section | Item | Acceptance Criteria | Evidence | Responsible | Status |
|---------|------|-------------------|----------|-------------|--------|
| 17.11 | Development Docker Compose stable | docker compose up starts all services (app, db, redis, celery worker) without errors; hot reload works | CI pipeline runs docker compose up and health check passes; developer verified on fresh clone | Platform Team + DevOps | Pending |
| 17.11 | Local developer setup documented | README with step-by-step setup: clone, venv, pip install, .env, docker compose, run migrations, run tests | docs/DEVELOPMENT_SETUP.md reviewed by 2 new developers for completeness | Platform Team | Pending |
| 17.11 | Pre-commit hooks configured (ruff, mypy, black) | .pre-commit-config.yaml with ruff, mypy, black hooks; pre-commit run --all-files passes | Pre-commit config file committed; CI runs pre-commit checks; new commits must pass hooks | Platform Team + Backend Team | Pending |
| 17.11 | CI pipeline configured with lint, typecheck, test stages | CI config (GitHub Actions / GitLab CI) with 4 stages: lint (ruff), typecheck (mypy strict), unit test, integration test | CI workflow file in .github/ or .gitlab-ci/; pipeline passes for sample PR | Platform Team + DevOps | Pending |


# 18. Engineering Review

**Reviewer:** Lead Architect
**Date:** 2026-06-30
**Phase:** Pre-Implementation Blueprint Review
**Target Score:** 9.8/10

---

## 18.1 Maintainability (Score: 9.6/10)

**Strengths:**
- Package structure follows a strict hexagonal architecture with clear layer boundaries (api -> application -> domain -> infrastructure). Every package has a defined ownership layer, allowed dependencies, and forbidden imports.
- Dependency rules (Section 12) are enforced at four levels: compile (mypy strict), lint (ruff + import-linter), test (pytest-arch), and runtime (import hook). All 20 rules are automated with zero-exception policy.
- The folder ownership table (Section 11) provides unambiguous guidance for every module's import scope. A new engineer can determine package responsibilities by reading the ownership matrix.
- Modular aggregate design with 9 bounded contexts, each owning its repository, events, tables, and APIs. Team ownership is clear.

**Weaknesses:**
- Memory aggregate boundary is ambiguous. Section 3 excludes Memory as a first-class aggregate (it is described as a child of Conversation), yet Section 4.4 defines memory-specific command handlers (UpdateMemory, ConfirmMemoryField), a MemoryService, a MemoryRepository, and a MemoryUpdateSaga. The schema in Section 10.2 places memory_fields under Conversation ownership, but the application layer treats Memory as an independent command boundary. This creates confusion about whether Memory is a sub-aggregate or a full aggregate. A new engineer will struggle to determine the correct place to add a new memory feature.
- The agents/ and tools/ packages have "Agent Layer" as their owner, which is not one of the four canonical DDD layers (API, Application, Domain, Infrastructure). This introduces a fifth layer with ambiguous dependency enforcement.

**Recommendation:** Resolve the Memory boundary by either (a) promoting Memory to a first-class aggregate with its own root, repository, schema ownership, and extraction strategy, or (b) demoting the memory command handlers to domain services within the Conversation aggregate and eliminating the standalone MemoryService. Codify the Agent Layer as an official fifth layer in the dependency enforcement configuration, or merge it into the Application layer.

---

## 18.2 Scalability (Score: 9.2/10)

**Strengths:**
- Celery workers are independently scalable per domain (8 worker pools with dedicated queues). Each worker has defined concurrency, rate limits, and graceful shutdown (Section 8).
- Database partitioning strategy is well-defined: BY tenant_id (list) + RANGE BY created_at (monthly) for high-volume tables. Retention policies are clear with archival paths to cold storage.
- Query handlers use cache-aside pattern with Redis, reducing DB load significantly. Read models bypass the domain layer entirely, keeping read paths lightweight.
- Conversation lock design prevents concurrent write conflicts across instances.

**Weaknesses:**
- Redis is a single point of failure for 7 critical concerns: broker for all Celery queues, cache for all read models, distributed locks, rate limiting, session storage, meeting availability bitmaps, worker heartbeats, and saga state. Section 9's failover behaviors consistently state "on Redis node failure, degrade to..." but the degradation is severe: every read hits the database, rate limiting is bypassed, sessions are lost, and locks are unavailable. The blueprint references the Redlock algorithm (requires 3 of 5 nodes) but never specifies the Redis cluster topology (number of nodes, replication factor, sharding strategy, persistence configuration). This is the single largest scalability risk.
- The conversation write lock (conversation:{id}:lock, TTL 30s) blocks concurrent message appends to the same conversation. For a high-traffic conversation with multiple participants sending messages simultaneously, the 3-retry backoff (100ms, 200ms, 400ms) adds 700ms of worst-case latency before returning 429. A real-time chat system at 1000 concurrent conversations could see significant lock contention on active conversations.
- The HandleMessage saga executes synchronously through 4 steps (persist, classify, memory, LLM). While the saga is Celery-driven, the lock is held for the entire duration. This limits throughput per conversation.

**Recommendation:** (a) Define the Redis cluster topology explicitly: minimum 3 master / 3 replica nodes, persistence with AOF (fsync every 1s) + RDB (every 5 min), and a dedicated Redis instance for Celery broker (to isolate queue throughput from cache/lock operations). (b) Replace the pessimistic lock on conversations with an optimistic concurrency model using aggregate version numbers. Only lock during the actual write (step 3), not during the full saga. (c) Document Redis cluster slot distribution to ensure conversation, meeting, and workflow keys are evenly distributed.

---

## 18.3 Testability (Score: 9.7/10)

**Strengths:**
- Domain aggregates are pure Python with zero external dependencies. They can be unit-tested without infrastructure, mocks, or fixtures. Aggregate methods accept and return value objects only.
- Repository interfaces are defined in the domain layer, making them trivially mockable. Application services receive repositories via constructor injection (dataclass pattern). Command handlers can be tested in isolation by injecting mock repositories.
- The testing strategy defines three levels (unit, integration, e2e) with specific tools (pytest, testcontainers, httpx AsyncClient) and coverage targets (90%, 80%, 70%). Factory fixtures (ConversationFactory) are specified.
- Architectural tests with pytest-arch verify dependency rules at test time (Section 12.3). This catches structural violations before code review.

**Weaknesses:**
- Saga coordinator testing is not defined. Section 14 lists saga compensation testing as a high-risk item (step 35), but the testing strategy (Section 13.10) does not specify how sagas will be tested. Sagas span multiple aggregates, queues, and Celery tasks. Without a saga test harness, compensation paths will be undertested.
- The blueprint mentions contract testing in the dimension header (18.3) but does not define a contract testing strategy anywhere in the document. Consumer-driven contract tests (e.g., Pact) would be valuable for the internal APIs between bounded contexts.

**Recommendation:** Add a saga testing section: use an in-memory event bus and fake Celery task runner to test saga steps and compensation paths without infrastructure. Specify contract testing with Pact or Spring Cloud Contract for all internal APIs (Section 3.x's internal endpoints).

---

## 18.4 Developer Experience (Score: 9.3/10)

**Strengths:**
- Coding conventions are exhaustive (Section 13): naming, packages, exceptions, logging, DI, configuration, repositories, DTOs, mappers, testing, documentation. Every contributor has a single reference for standards.
- The folder ownership table (Section 11) maps every directory to its owner layer, allowed/forbidden imports, and dependency direction. This is the fastest onboarding aid available.
- The implementation order (Section 14) provides a clear 6-phase, 40-step sequence with effort estimates, prerequisites, and risk levels. A new engineer can see exactly what to build and in what order.

**Weaknesses:**
- There is no quickstart guide or local setup script in the blueprint. Section 14's Phase 1 includes scaffolding but does not specify Docker Compose configuration, environment variable templates, or a "getting started" sequence that gets a developer running in under 15 minutes.
- Architecture Decision Records (ADRs) are referenced in Section 13.11 but none exist yet. Key decisions (Redis as broker vs RabbitMQ, PostgreSQL vs Cosmos DB, event bus protocol choice) should have ADRs before implementation begins, so new engineers can understand the rationale.
- The blueprint lacks a troubleshooting or FAQ section for common setup issues.

**Recommendation:** Add a Docker Compose file for local development (PostgreSQL + Redis + Celery worker + API) as part of Phase 1. Publish ADR-001 (Event Bus Protocol Decision), ADR-002 (Redis Topology Decision), and ADR-003 (Memory Aggregate Boundary Decision) before Phase 2 begins.

---

## 18.5 Extensibility (Score: 9.6/10)

**Strengths:**
- Tool registry pattern (tools/) allows adding new tools by implementing a Tool interface and registering with the registry. No core code changes required. Tools are executed by ToolExecutionService through a generic pipeline.
- Model router with 5-tier classification (Section 4.7's ClassifyIntent) supports adding new model providers by implementing the LLM client adapter. The router already has fallback logic.
- Bounded contexts are well-separated with defined dependencies (Section 3 Summary). New contexts can be added by creating a new aggregate, repository, event handlers, and API endpoints without modifying existing contexts.
- The event-driven architecture supports extensibility: new consumers can subscribe to existing events without modifying producers. The fan-out pattern in MeetingScheduled (4 branches) demonstrates this.

**Weaknesses:**
- Adding a new tool requires modifying the ClassifyIntent prompt to include the new tool in the intent classification few-shot examples. This couples tool registration with prompt management. A truly extensible system would discover available tools dynamically and include them in the classification prompt automatically.
- The event bus protocol ambiguity (see Microservice Readiness) means that the extensibility mechanism for cross-context communication is not well-defined. New contexts need to know whether to publish to Redis Pub/Sub, Celery queues, or a message broker.

**Recommendation:** Implement a tool discovery mechanism that generates the intent classification prompt dynamically from the tool registry. This decouples tool registration from prompt maintenance. Define the event bus protocol unambiguously so new bounded contexts have a clear integration contract.

---

## 18.6 Microservice Readiness (Score: 8.8/10)

**Strengths:**
- Bounded contexts are cleanly separated with unambiguous aggregate boundaries, repository ownership, and database schema ownership. The aggregate dependency graph (Section 3 Summary) is acyclic and clearly hierarchical (Tenant -> UserProfile -> others).
- Each aggregate owns its events, commands, and queries. The extraction strategy column in the Package Ownership Matrix specifies how each package would be extracted (e.g., "Extract into shared domain library"). Repository implementations are already separated per aggregate.
- Internal APIs are defined separately from public APIs, providing explicit integration points between bounded contexts (Section 3.x Internal APIs).

**Weaknesses:**
- The event bus protocol is not well-defined. The blueprint uses queue patterns (queue:conversation.events), Redis Pub/Sub (meeting:{id}:events), Celery task routing, and n8n webhooks, but never specifies the primary event transport. For microservice extraction, each bounded context needs a well-defined protocol for publishing and consuming events. Currently, events are tightly coupled to the Celery/Redis infrastructure. Extracting the Meeting context into a standalone service would require re-engineering event delivery to the Workflow context.
- Shared kernel dependencies are not minimized. The agent layer (agents/, tools/, memory/, rag/) depends on domain/, services/, and config/. Extracting agents into a microservice would require extracting domain value objects, domain events, and application-level services as shared libraries. The blueprint does not specify which domain components form the shared kernel and how they are versioned.
- The services/ package (application-level business services) sits ambiguously between the Application and Domain layers. Section 11 shows services/ owned by the Application layer, but Section 2's layer mapping does not include it. Services have access to infrastructure (via domain interfaces), which makes them unsuitable for extraction into a pure microservice.

**Recommendation:** (a) Select and document the event bus protocol: recommend RabbitMQ with topic exchanges for domain events, or Apache Kafka for event sourcing. Redis Pub/Sub should be reserved for real-time (typing indicators, live transcripts), not domain event delivery. (b) Define the shared kernel explicitly: list every domain value object and domain event that is shared across bounded contexts. Specify that these live in a separate shared-kernel package with semantic versioning. (c) Eliminate the services/ package by merging its responsibilities into application/services/ or refactoring into domain services.

---

## 18.7 Cloud Readiness (Score: 9.2/10)

**Strengths:**
- Stateless API design: all application instances are stateless. Session state lives in Redis, not in-memory. This enables horizontal scaling and deployment to any cloud provider.
- PostgreSQL and Redis are cloud-managed compatible (RDS, ElastiCache, Cloud SQL, Memorystore, Azure Database, Azure Cache for Redis). Infrastructure adapters abstract provider-specific details.
- Blob storage for documents (S3, Azure Blob, GCS) is referenced. Archive strategy uses cold storage (S3 Glacier, Azure Archive).
- Containerized deployment is planned (Docker Compose, CI/CD pipeline referenced in Phase 6).

**Weaknesses:**
- No cloud-agnostic abstraction for blob storage. The blueprint mentions "S3/BlobStorageClient" and "S3 Glacier / Azure Archive" without defining a common storage interface. Vendor lock-in is a real risk for the document storage and archival paths.
- No multi-region deployment strategy. The blueprint does not address active-active vs active-passive, cross-region replication, or DNS-based traffic routing. For a Phase 3.5 system targeting global availability, this is a gap.
- No cloud cost model. The blueprint specifies retention policies (7 years for audit_logs at 500+ events/day) and async transcription (GPU workers), but does not estimate cloud costs or specify budget limits. A lead architect review should flag cost implications before implementation.

**Recommendation:** Abstract blob storage behind a StorageAdapter interface (domain layer) with implementations for S3, Azure Blob, and GCS. Document the multi-region strategy: active-passive with PostgreSQL read replicas and Redis Global Datastore for the active region. Add a cost estimation section to Phase 6 that models infrastructure costs at expected load (1000 concurrent conversations, 480 messages/min peak).

---

## 18.8 AI Readiness (Score: 9.7/10)

**Strengths:**
- Model routing strategy with 5 tiers (ClassifyIntent) is future-proof. Adding a new model provider requires only an adapter implementation and a router configuration entry. The circuit breaker pattern (CircuitBreakerOpened event) protects against provider failures.
- Fallback paths are defined for every AI failure mode: intent classification falls back to rule-based classifier, LLM response generation falls back to a graceful message, tool execution failures inform the user, embedding failures flag for offline reindexing. The HandleMessage saga has explicit compensation steps for each failure scenario.
- Prompt registry (PromptVersion aggregate) manages versioning correctly: immutable versions, promotion to production, rollback, diff, evaluation, and backtesting. The cache key (prompt:active:{prompt_id}) provides sub-millisecond active prompt resolution.
- Memory strategy is comprehensive: short-term (conversation buffer in Redis, TTL 1h), long-term (PostgreSQL-backed, field-level with confirmation policy), semantic (vector embeddings with cross-encoder re-ranking). The memory update saga with confirmation tokens demonstrates mature design.

**Weaknesses:**
- No A/B testing framework for prompt versions. The blueprint supports evaluating prompts (evaluate_prompt_version task) and promoting to production, but does not describe how to run A/B tests where a percentage of traffic sees the new prompt and the rest sees the current production prompt. Canary releases for LLM prompts are critical for safe deployment.
- The prompt test results schema (prompt_test_results) captures evaluation scores but does not define pass/fail criteria. Without a threshold for what constitutes a passing evaluation, the promote-to-production pipeline is subjective.

**Recommendation:** Add a canary release mechanism to the prompt registry: support traffic splitting (e.g., 5% of conversations use prompt v3, 95% use v2) with automated rollback if evaluation metrics drop below threshold. Define evaluation pass/fail criteria in the prompt_test_results schema (minimum accuracy, maximum latency, maximum token usage).

---

## 18.9 Operational Readiness (Score: 9.2/10)

**Strengths:**
- Monitoring is designed with Prometheus metrics, structured JSON logging, and OpenTelemetry tracing. Health check endpoints (/health, /metrics) are defined per layer.
- Worker graceful shutdown protocol (Section 8.5) is comprehensive: 4-phase shutdown with warm timeout, connection pool drain, and process exit with exit code signaling. This is production-grade.
- Dead letter queues are defined for every event type with TTL, replay mechanisms (automatic and manual), and monitoring thresholds (alert on >100 messages). Section 6.6 provides a clear architecture diagram.
- Retry policies (Section 6.4) are well-defined per event type with exponential backoff, jitter, and max attempts.

**Weaknesses:**
- Disaster recovery plan is not documented. The blueprint does not define Recovery Time Objective (RTO) or Recovery Point Objective (RPO) for any component. While the failover behaviors in Section 9 describe degraded modes, there is no holistic DR plan covering region failure, data corruption, or cascading service failure.
- Runbooks are referenced in the handoff protocol (Section 15.3.4) but none are defined. Common failure scenarios (e.g., Redis cluster failure, LLM provider outage, database connection exhaustion) do not have documented response procedures.
- The deployment pipeline is listed as step 38 but is not designed in the blueprint. There is no CI/CD architecture (GitHub Actions vs GitLab CI vs Jenkins), no artifact repository strategy, no environment promotion model, and no rollback procedure.

**Recommendation:** Define RTO (target: 1 hour) and RPO (target: 5 minutes) for the system, and document a DR plan covering: (a) multi-region failover, (b) database point-in-time recovery, (c) Redis cluster rebuild, (d) event replay from dead letter queues after recovery. Create a runbook template for the top 5 failure scenarios (Redis down, PostgreSQL down, LLM provider outage, Celery worker crash, n8n unreachable). Design the deployment pipeline with at minimum: staging environment with production-like data, canary deployment step, automated rollback on health check failure, and database migration safety guarantees.

---

## 18.10 Overall Score and Verdict

| Dimension | Score | Meets 9.8 Target? |
|-----------|-------|-------------------|
| 18.1 Maintainability | 9.6/10 | No (memory boundary ambiguity) |
| 18.2 Scalability | 9.2/10 | No (Redis single point of failure, lock contention) |
| 18.3 Testability | 9.7/10 | No (saga testing undefined, no contract testing) |
| 18.4 Developer Experience | 9.3/10 | No (no quickstart, no ADRs) |
| 18.5 Extensibility | 9.6/10 | No (tool-prompt coupling, event bus undefined) |
| 18.6 Microservice Readiness | 8.8/10 | No (event bus protocol undefined, shared kernel not minimized) |
| 18.7 Cloud Readiness | 9.2/10 | No (no blob storage abstraction, no multi-region, no cost model) |
| 18.8 AI Readiness | 9.7/10 | No (no A/B testing for prompts) |
| 18.9 Operational Readiness | 9.2/10 | No (no DR plan, no runbooks, deployment pipeline not designed) |
| **Average** | **9.37/10** | No |

**What must improve to reach 9.8/10:**

1. **Microservice Readiness (8.8)** is the largest gap. The event bus protocol must be unambiguously defined (recommend RabbitMQ topic exchanges for domain events, Redis Pub/Sub for real-time only). The shared kernel must be explicitly enumerated and versioned. The services/ package must be eliminated or properly layered. This alone lifts the average by ~0.15 points.

2. **Scalability (9.2) and Operational Readiness (9.2)** are tied for the second-largest gap. Define the Redis cluster topology (3 master / 3 replica minimum, dedicated broker instance). Document the DR plan with RTO/RPO and runbooks for the top 5 failure scenarios. Design the deployment pipeline. These lift the average by ~0.13 points.

3. **Developer Experience (9.3) and Cloud Readiness (9.2)** need ADRs published, a Docker Compose quickstart added, a storage abstraction interface defined, and a multi-region strategy documented. These lift the average by ~0.10 points.

**Gaps discovered during this review:**

- **Gap 1: Memory aggregate boundary contradiction.** The Conversation aggregate (Section 3.1) does not list Memory as a sub-component, but the database schema (Section 10.2) shows memory_fields owned by the Conversation aggregate. Meanwhile, Section 4.4 defines Memory commands with their own service, repository, and saga. This ambiguity will cause merge conflicts when two teams simultaneously work on conversation features and memory features. Fix: choose one canonical model.

- **Gap 2: Event bus protocol undefined.** The blueprint uses three overlapping event transport mechanisms (Redis lists for Celery tasks, Redis Pub/Sub for real-time, n8n webhooks for external integration) without defining which is the primary mechanism for domain event delivery. The queue names follow a consistent pattern (queue:{domain}.events) but the transport layer is never specified. This blocks microservice extraction and confuses cross-team integration work. Fix: specify RabbitMQ or Kafka as the primary event bus and document the event schema contract (CloudEvents format recommended).

**Verdict: Conditional**

Approved for Phase 1 (Foundation) implementation only. Phase 2 (Domain & Infrastructure) is blocked until the following conditions are met:

1. ADR-001 published resolving the event bus protocol with explicit transport selection and event schema contract.
2. ADR-002 published defining the Redis cluster topology, persistence configuration, and primary/failover behavior.
3. ADR-003 published resolving the Memory aggregate boundary ambiguity.
4. Quickstart Docker Compose configuration added to the blueprint.

Once these four conditions are satisfied, Phase 2 may begin. Re-review of the complete blueprint is required before Phase 5 (AI & Memory) to validate that the AI readiness gaps (prompt A/B testing, evaluation thresholds) have been addressed.



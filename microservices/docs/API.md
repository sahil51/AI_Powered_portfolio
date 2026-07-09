# AI Executive Assistant API

## Endpoints

### Health
- `GET /health/live` - Liveness check
- `GET /health/ready` - Readiness check
- `GET /health` - Full health check

### Chat
- `POST /chat/message` - Send a chat message (requires auth)
- `POST /chat/message/sync` - Send a chat message (no auth)

### Meetings
- `POST /meetings/schedule` - Schedule a meeting (requires auth)
- `GET /meetings/types` - Get available meeting types

### Leads
- `POST /leads/create` - Create a lead (requires auth)

### Memory
- `GET /memory/profile/{user_id}` - Get user profile (requires auth)
- `PATCH /memory/profile/{user_id}` - Update user profile (requires auth)

### Workflows
- `POST /workflows/trigger` - Trigger an n8n workflow
- `GET /workflows/status/{workflow_id}` - Get workflow status

## Architecture

```
User -> Chat Widget -> AI Gateway -> FastAPI -> LangGraph -> LiteLLM -> LLM
                                                              |
                                                    Celery -> n8n -> External Services
```

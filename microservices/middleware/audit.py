from monitoring.logger import logger


async def log_audit(
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    user_id: str | None = None,
    conversation_id: str | None = None,
    metadata: dict | None = None,
):
    logger.info(
        f"AUDIT: {action} on {entity_type}",
        extra={
            "audit": True,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "metadata": metadata or {},
        },
    )

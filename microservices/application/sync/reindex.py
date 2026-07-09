import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from application.sync.checksum import PORTFOLIO_TABLES, save_checksum
from monitoring.logger import logger
from rag.embeddings.service import EmbeddingService

DOC_TITLE = "portfolio_data"


async def reindex_portfolio_data(session: AsyncSession, redis_client) -> dict:
    embedder = EmbeddingService()
    now = datetime.now(timezone.utc)

    items = []
    hero = (await session.execute(sa_text("SELECT * FROM portfolio_heroinfo LIMIT 1"))).first()
    if hero:
        h = hero._mapping
        text = (
            f"Sahil Thakur - {h.get('role', '')}. "
            f"Location: {h.get('location', '')}. "
            f"Current Company: {h.get('current_company', '')}. "
            f"About: {h.get('about_me', '')}. "
            f"Tech Stack: {h.get('tech_stack', '')}. "
            f"AI Expertise: {h.get('ai_expertise', '')}. "
            f"Experience: {h.get('experience_years', 0)} years. "
            f"Projects Completed: {h.get('projects_completed', 0)}. "
            f"AI Agents Built: {h.get('ai_agents_built', 0)}."
        )
        items.append({"title": "About Sahil Thakur", "section": "hero", "text": text, "tags": ["hero", "about"]})

    projects = (await session.execute(sa_text("SELECT * FROM portfolio_project ORDER BY number"))).all()
    for proj in projects:
        p = proj._mapping
        text = f"Project: {p.get('title', '')}. Description: {p.get('description', '')}. Technologies: {p.get('technologies', '')}"
        items.append({"title": f"Project: {p.get('title', '')}", "section": "project", "text": text, "tags": ["project", "portfolio"]})

    experiences = (await session.execute(sa_text("SELECT * FROM portfolio_experience ORDER BY start_date DESC"))).all()
    for exp in experiences:
        e = exp._mapping
        text = f"Experience: {e.get('role', '')} at {e.get('company', '')}. Location: {e.get('location', '')}. Period: {e.get('start_date', '')} - {e.get('end_date', 'Present')}. Intro: {e.get('intro', '')}. Contributions: {e.get('key_contributions', '')}. Technologies: {e.get('technologies', '')}"
        if e.get('company_projects'):
            text += f" Projects: {e.get('company_projects', '')}"
        items.append({"title": f"Experience: {e.get('role', '')} at {e.get('company', '')}", "section": "experience", "text": text, "tags": ["experience", "work"]})

    categories = (await session.execute(sa_text("SELECT * FROM portfolio_skillcategory"))).all()
    for cat in categories:
        c = cat._mapping
        skills_result = await session.execute(sa_text("SELECT name FROM portfolio_skill WHERE category_id = :cid"), {"cid": c.get("id")})
        skill_names = [row[0] for row in skills_result]
        text = f"Skill Category: {c.get('name', '')}. Skills: {', '.join(skill_names)}"
        items.append({"title": f"Skills: {c.get('name', '')}", "section": "skill", "text": text, "tags": ["skill", c.get('name', '').lower()]})

    education = (await session.execute(sa_text("SELECT * FROM portfolio_education"))).all()
    for edu in education:
        e = edu._mapping
        text = f"Education: {e.get('degree', '')} at {e.get('institution', '')}. Duration: {e.get('duration', '')}. Location: {e.get('location', '')}. Scores: {e.get('scores', '')}"
        items.append({"title": f"Education: {e.get('degree', '')}", "section": "education", "text": text, "tags": ["education"]})

    blogs = (await session.execute(sa_text("SELECT * FROM portfolio_blogpost WHERE status = 'Published' ORDER BY id DESC"))).all()
    for blog in blogs:
        b = blog._mapping
        text = f"Blog: {b.get('title', '')}. Summary: {b.get('summary', '')}"
        items.append({"title": f"Blog: {b.get('title', '')}", "section": "blog", "text": text, "tags": ["blog"]})

    contacts = (await session.execute(sa_text("SELECT * FROM portfolio_contactmethod ORDER BY \"order\""))).all()
    for contact in contacts:
        c = contact._mapping
        text = f"Contact: {c.get('name', '')} - {c.get('value', '')}"
        items.append({"title": f"Contact: {c.get('name', '')}", "section": "contact", "text": text, "tags": ["contact"]})

    existing = await session.execute(
        sa_text("SELECT id FROM knowledge_documents WHERE title = :title AND is_deleted = FALSE"),
        {"title": DOC_TITLE},
    )
    existing_doc = existing.first()

    doc_id = existing_doc[0] if existing_doc else uuid.uuid4()

    if existing_doc:
        await session.execute(sa_text("DELETE FROM knowledge_chunks WHERE document_id = :did"), {"did": doc_id})
        await session.execute(
            sa_text("UPDATE knowledge_documents SET updated_at = :now WHERE id = :did"),
            {"now": now, "did": str(doc_id)},
        )
    else:
        await session.execute(
            sa_text("""
                INSERT INTO knowledge_documents (id, is_deleted, version, title, doc_type, status, language, created_at, updated_at)
                VALUES (:id, FALSE, 1, :title, 'db_ingest', 'active', 'en', :now, :now)
            """),
            {"id": str(doc_id), "title": DOC_TITLE, "now": now},
        )

    chunk_index = 0
    for item in items:
        for chunk_text in _chunk_text(item["text"], 2000):
            try:
                embedding = await embedder.embed_text(chunk_text)
                await session.execute(
                    sa_text("""
                        INSERT INTO knowledge_chunks
                            (id, is_deleted, version, document_id, chunk_index, text, section, heading, chunk_metadata,
                             embedding_status, embedding, embedding_dimension, embedding_model,
                             language, created_at, updated_at)
                        VALUES
                            (:id, FALSE, 1, :doc_id, :chunk_index, :text, :section, :heading, :chunk_metadata,
                             'completed', :embedding, :dim, :model,
                             'en', :now, :now)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "doc_id": str(doc_id),
                        "chunk_index": chunk_index,
                        "text": chunk_text,
                        "section": item["section"],
                        "heading": item["title"],
                        "chunk_metadata": json.dumps(item["tags"]),
                        "embedding": str(embedding),
                        "dim": len(embedding),
                        "model": "text-embedding-004",
                        "now": now,
                    },
                )
                chunk_index += 1
            except Exception as e:
                logger.warning(f"Failed to embed chunk '{item['title']}': {e}")

    await session.execute(
        sa_text("UPDATE knowledge_documents SET embedded_at = :now, indexed_at = :now WHERE id = :id"),
        {"now": now, "id": str(doc_id)},
    )

    new_checksum = await _compute_checksum(session)
    try:
        save_checksum(redis_client, new_checksum)
    except Exception as e:
        logger.warning(f"Failed to save checksum: {e}")

    return {"chunks_created": chunk_index, "items_ingested": len(items)}


async def _compute_checksum(session: AsyncSession) -> str:
    import hashlib

    hasher = hashlib.sha256()
    for table in PORTFOLIO_TABLES:
        rows = await session.execute(sa_text(f"SELECT * FROM {table} ORDER BY id"))
        for row in rows:
            hasher.update(str(dict(row._mapping)).encode())
    return hasher.hexdigest()


def _chunk_text(text: str, max_chars: int = 2000) -> list[str]:
    words = text.split()
    chunks = []
    current = []
    current_len = 0
    for word in words:
        if current_len + len(word) + 1 > max_chars and current:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += len(word) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks or [text]

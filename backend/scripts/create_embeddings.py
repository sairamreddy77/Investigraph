#!/usr/bin/env python3
"""
Embedding migration script for POLE crime investigation graph.

Creates vector embeddings on Crime nodes and builds a Neo4j vector index.
Designed to be run standalone (not as part of app startup).

Usage:
    cd backend
    python -m scripts.create_embeddings

Environment variables required (from .env):
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE
"""
import os
import sys
import logging
import time

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from neo4j import GraphDatabase
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# ──── Configuration ─────────────────────────────────────

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "pole")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
VECTOR_DIMENSIONS = int(os.getenv("VECTOR_DIMENSIONS", "384"))
INDEX_NAME = "crime_vector_index"

BATCH_SIZE = 100


def create_vector_index(driver, index_name: str, label: str, property_name: str, dimensions: int):
    """Create a vector index in Neo4j if it doesn't exist."""
    logger.info(f"Creating vector index '{index_name}' on :{label}.{property_name} ({dimensions} dims)...")

    with driver.session(database=NEO4J_DATABASE) as session:
        # Check if index exists
        result = session.run("SHOW INDEXES YIELD name RETURN name")
        existing = [r["name"] for r in result]
        if index_name in existing:
            logger.info(f"Index '{index_name}' already exists, skipping creation")
            return

        # Create vector index
        session.run(f"""
            CREATE VECTOR INDEX `{index_name}`
            FOR (n:{label})
            ON (n.{property_name})
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {dimensions},
                    `vector.similarity_function`: 'cosine'
                }}
            }}
        """)
        logger.info(f"Vector index '{index_name}' created successfully")


def build_text_for_crime(crime: dict) -> str:
    """Build text representation of a Crime node for embedding."""
    parts = []
    if crime.get("type"):
        parts.append(f"Crime type: {crime['type']}")
    if crime.get("last_outcome"):
        parts.append(f"Outcome: {crime['last_outcome']}")
    if crime.get("note") and crime["note"].strip():
        parts.append(f"Note: {crime['note']}")
    if crime.get("charge") and crime["charge"].strip():
        parts.append(f"Charge: {crime['charge']}")
    if crime.get("date"):
        parts.append(f"Date: {crime['date']}")

    return ". ".join(parts) if parts else "Crime record"


def embed_crime_nodes(driver, embedder):
    """Generate and store embeddings for all Crime nodes."""
    logger.info("Counting Crime nodes...")

    with driver.session(database=NEO4J_DATABASE) as session:
        count_result = session.run("MATCH (c:Crime) RETURN count(c) AS total")
        total = count_result.single()["total"]
        logger.info(f"Found {total} Crime nodes to embed")

    if total == 0:
        logger.warning("No Crime nodes found!")
        return

    # Check how many already have embeddings
    with driver.session(database=NEO4J_DATABASE) as session:
        embedded_result = session.run(
            "MATCH (c:Crime) WHERE c.embedding IS NOT NULL RETURN count(c) AS total"
        )
        already_embedded = embedded_result.single()["total"]
        if already_embedded == total:
            logger.info(f"All {total} Crime nodes already have embeddings, skipping")
            return
        elif already_embedded > 0:
            logger.info(f"{already_embedded}/{total} already embedded, processing remaining")

    offset = 0
    embedded_count = 0
    start_time = time.time()

    while offset < total:
        with driver.session(database=NEO4J_DATABASE) as session:
            # Fetch batch of Crime nodes without embeddings
            result = session.run("""
                MATCH (c:Crime)
                WHERE c.embedding IS NULL
                RETURN c.id AS id, c.type AS type, c.date AS date,
                       c.last_outcome AS last_outcome, c.note AS note,
                       c.charge AS charge
                LIMIT $batch_size
            """, {"batch_size": BATCH_SIZE})

            batch = list(result)
            if not batch:
                break

            # Build text representations
            texts = [build_text_for_crime(dict(record)) for record in batch]
            ids = [record["id"] for record in batch]

            # Generate embeddings
            embeddings = embedder.embed_query_batch(texts) if hasattr(embedder, 'embed_query_batch') else [
                embedder.embed_query(text) for text in texts
            ]

            # Store embeddings
            for crime_id, embedding in zip(ids, embeddings):
                session.run("""
                    MATCH (c:Crime {id: $id})
                    SET c.embedding = $embedding
                """, {"id": crime_id, "embedding": embedding})

            embedded_count += len(batch)
            elapsed = time.time() - start_time
            rate = embedded_count / elapsed if elapsed > 0 else 0
            logger.info(
                f"Embedded {embedded_count}/{total} crimes "
                f"({embedded_count/total*100:.1f}%) "
                f"[{rate:.1f} nodes/sec]"
            )

        offset += BATCH_SIZE

    elapsed = time.time() - start_time
    logger.info(f"Embedding complete: {embedded_count} nodes in {elapsed:.1f}s")


def main():
    if not NEO4J_URI or not NEO4J_PASSWORD:
        logger.error("NEO4J_URI and NEO4J_PASSWORD must be set in environment or .env file")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("POLE Crime Graph - Embedding Migration")
    logger.info("=" * 60)
    logger.info(f"Neo4j URI: {NEO4J_URI}")
    logger.info(f"Database: {NEO4J_DATABASE}")
    logger.info(f"Embedding model: {EMBEDDING_MODEL}")
    logger.info(f"Vector dimensions: {VECTOR_DIMENSIONS}")
    logger.info(f"Index name: {INDEX_NAME}")
    logger.info("=" * 60)

    # Connect to Neo4j
    logger.info("Connecting to Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    driver.verify_connectivity()
    logger.info("Connected")

    # Verify Neo4j version
    with driver.session(database=NEO4J_DATABASE) as session:
        result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions")
        for record in result:
            logger.info(f"  {record['name']}: {record['versions']}")

    # Initialize embedder
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL}...")
    from neo4j_graphrag.embeddings import SentenceTransformerEmbeddings
    embedder = SentenceTransformerEmbeddings(model=EMBEDDING_MODEL)
    logger.info("Embedder loaded")

    # Step 1: Create vector index
    create_vector_index(driver, INDEX_NAME, "Crime", "embedding", VECTOR_DIMENSIONS)

    # Step 2: Embed Crime nodes
    embed_crime_nodes(driver, embedder)

    # Step 3: Verify
    logger.info("Verifying embeddings...")
    with driver.session(database=NEO4J_DATABASE) as session:
        result = session.run(
            "MATCH (c:Crime) WHERE c.embedding IS NOT NULL RETURN count(c) AS embedded"
        )
        count = result.single()["embedded"]
        logger.info(f"Verified: {count} Crime nodes have embeddings")

    # Verify index
    with driver.session(database=NEO4J_DATABASE) as session:
        result = session.run("SHOW INDEXES YIELD name, type WHERE name = $name RETURN name, type",
                             {"name": INDEX_NAME})
        for record in result:
            logger.info(f"Index '{record['name']}' exists (type: {record['type']})")

    driver.close()
    logger.info("Migration complete!")


if __name__ == "__main__":
    main()

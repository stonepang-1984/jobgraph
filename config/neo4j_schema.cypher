// ============================================================
// Neo4j Schema Definition for Multimodal Graph RAG
// ============================================================

// ============================================================
// 1. Constraints (Unique IDs)
// ============================================================

CREATE CONSTRAINT document_id IF NOT EXISTS
FOR (d:Document) REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT text_chunk_id IF NOT EXISTS
FOR (c:TextChunk) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT image_id IF NOT EXISTS
FOR (i:Image) REQUIRE i.id IS UNIQUE;

CREATE CONSTRAINT table_id IF NOT EXISTS
FOR (t:Table) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT video_segment_id IF NOT EXISTS
FOR (v:VideoSegment) REQUIRE v.id IS UNIQUE;

CREATE CONSTRAINT audio_segment_id IF NOT EXISTS
FOR (a:AudioSegment) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT entity_id IF NOT EXISTS
FOR (e:Entity) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT community_id IF NOT EXISTS
FOR (c:Community) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT topic_id IF NOT EXISTS
FOR (t:Topic) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT source_id IF NOT EXISTS
FOR (s:Source) REQUIRE s.id IS UNIQUE;


// ============================================================
// 2. Indexes for Performance
// ============================================================

// Entity name index
CREATE INDEX entity_name IF NOT EXISTS
FOR (e:Entity) ON (e.name);

// Entity type index
CREATE INDEX entity_type IF NOT EXISTS
FOR (e:Entity) ON (e.type);

// Document status index
CREATE INDEX document_status IF NOT EXISTS
FOR (d:Document) ON (d.status);

// Document file_type index
CREATE INDEX document_file_type IF NOT EXISTS
FOR (d:Document) ON (d.file_type);


// ============================================================
// 3. Fulltext Indexes
// ============================================================

CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS
FOR (e:Entity) ON EACH [e.name, e.description];

CREATE FULLTEXT INDEX text_chunk_fulltext IF NOT EXISTS
FOR (c:TextChunk) ON EACH [c.content];

CREATE FULLTEXT INDEX community_fulltext IF NOT EXISTS
FOR (c:Community) ON EACH [c.title, c.summary];


// ============================================================
// 4. Vector Indexes
// ============================================================

// Text chunk embedding
CREATE VECTOR INDEX text_chunk_embedding IF NOT EXISTS
FOR (c:TextChunk) ON (c.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1024,
        `vector.similarity_function`: 'cosine'
    }
};

// Image visual embedding (CLIP)
CREATE VECTOR INDEX image_visual_embedding IF NOT EXISTS
FOR (i:Image) ON (i.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 768,
        `vector.similarity_function`: 'cosine'
    }
};

// Image text embedding (caption/OCR)
CREATE VECTOR INDEX image_text_embedding IF NOT EXISTS
FOR (i:Image) ON (i.text_embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1024,
        `vector.similarity_function`: 'cosine'
    }
};

// Table embedding
CREATE VECTOR INDEX table_embedding IF NOT EXISTS
FOR (t:Table) ON (t.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1024,
        `vector.similarity_function`: 'cosine'
    }
};

// Video segment embedding
CREATE VECTOR INDEX video_segment_embedding IF NOT EXISTS
FOR (v:VideoSegment) ON (v.transcript_embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1024,
        `vector.similarity_function`: 'cosine'
    }
};

// Audio segment embedding
CREATE VECTOR INDEX audio_segment_embedding IF NOT EXISTS
FOR (a:AudioSegment) ON (a.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1024,
        `vector.similarity_function`: 'cosine'
    }
};

// Entity embedding
CREATE VECTOR INDEX entity_embedding IF NOT EXISTS
FOR (e:Entity) ON (e.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1024,
        `vector.similarity_function`: 'cosine'
    }
};

// Community embedding
CREATE VECTOR INDEX community_embedding IF NOT EXISTS
FOR (c:Community) ON (c.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1024,
        `vector.similarity_function`: 'cosine'
    }
};

// Topic embedding
CREATE VECTOR INDEX topic_embedding IF NOT EXISTS
FOR (t:Topic) ON (t.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1024,
        `vector.similarity_function`: 'cosine'
    }
};

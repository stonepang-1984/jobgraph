"""People graph manager - CRUD operations for person entities."""

from typing import Optional
from loguru import logger

from src.graph.neo4j_client import neo4j_client
from src.graph.people.models import (
    Person,
    Company,
    University,
    WorkExperience,
    Education,
    PersonRelation,
)


class PeopleGraphManager:
    """Manage people-related entities and relationships in Neo4j."""

    # ============================================================
    # Person CRUD
    # ============================================================

    def create_person(self, person: Person) -> dict:
        """Create or update a person node."""
        cypher = """
        MERGE (p:Person {id: $id})
        SET p.name = $name,
            p.name_en = $name_en,
            p.gender = $gender,
            p.birth_date = $birth_date,
            p.birth_place = $birth_place,
            p.nationality = $nationality,
            p.bio = $bio,
            p.photo_url = $photo_url,
            p.tags = $tags,
            p.source = $source,
            p.source_url = $source_url,
            p.created_at = datetime(),
            p.updated_at = datetime()
        RETURN p
        """
        result = neo4j_client.execute_write(
            cypher,
            {
                "id": person.id,
                "name": person.name,
                "name_en": person.name_en,
                "gender": person.gender,
                "birth_date": person.birth_date,
                "birth_place": person.birth_place,
                "nationality": person.nationality,
                "bio": person.bio,
                "photo_url": person.photo_url,
                "tags": person.tags,
                "source": person.source,
                "source_url": person.source_url,
            },
        )
        logger.info(f"Created/updated person: {person.name}")
        return result

    def get_person(self, person_id: str) -> Optional[dict]:
        """Get person by ID."""
        cypher = """
        MATCH (p:Person {id: $id})
        OPTIONAL MATCH (p)-[r:WORKS_AT]->(c:Company)
        OPTIONAL MATCH (p)-[e:STUDIED_AT]->(u:University)
        RETURN p,
               collect(DISTINCT {
                   company: c.name,
                   position: r.position,
                   is_current: r.is_current
               }) AS work_history,
               collect(DISTINCT {
                   university: u.name,
                   degree: e.degree,
                   major: e.major
               }) AS education
        """
        results = neo4j_client.execute_query(cypher, {"id": person_id})
        return results[0] if results else None

    def search_persons(self, query: str, limit: int = 20) -> list[dict]:
        """Search persons by name."""
        cypher = """
        MATCH (p:Person)
        WHERE p.name CONTAINS $query
           OR p.name_en CONTAINS $query
           OR any(alias IN p.aliases WHERE alias CONTAINS $query)
        RETURN p
        ORDER BY p.name
        LIMIT $limit
        """
        return neo4j_client.execute_query(
            cypher, {"query": query, "limit": limit}
        )

    # ============================================================
    # Company CRUD
    # ============================================================

    def create_company(self, company: Company) -> dict:
        """Create or update a company node."""
        cypher = """
        MERGE (c:Company {id: $id})
        SET c.name = $name,
            c.name_en = $name_en,
            c.industry = $industry,
            c.size = $size,
            c.founded = $founded,
            c.headquarters = $headquarters,
            c.website = $website,
            c.description = $description,
            c.logo_url = $logo_url,
            c.tags = $tags,
            c.source = $source,
            c.created_at = datetime(),
            c.updated_at = datetime()
        RETURN c
        """
        result = neo4j_client.execute_write(
            cypher,
            {
                "id": company.id,
                "name": company.name,
                "name_en": company.name_en,
                "industry": company.industry,
                "size": company.size,
                "founded": company.founded,
                "headquarters": company.headquarters,
                "website": company.website,
                "description": company.description,
                "logo_url": company.logo_url,
                "tags": company.tags,
                "source": company.source,
            },
        )
        logger.info(f"Created/updated company: {company.name}")
        return result

    def get_company_employees(self, company_id: str) -> list[dict]:
        """Get all employees of a company."""
        cypher = """
        MATCH (p:Person)-[r:WORKS_AT]->(c:Company {id: $company_id})
        RETURN p.name AS name,
               p.id AS person_id,
               r.position AS position,
               r.start_date AS start_date,
               r.is_current AS is_current
        ORDER BY r.start_date DESC
        """
        return neo4j_client.execute_query(cypher, {"company_id": company_id})

    # ============================================================
    # University CRUD
    # ============================================================

    def create_university(self, university: University) -> dict:
        """Create or update a university node."""
        cypher = """
        MERGE (u:University {id: $id})
        SET u.name = $name,
            u.name_en = $name_en,
            u.location = $location,
            u.country = $country,
            u.ranking = $ranking,
            u.website = $website,
            u.description = $description,
            u.logo_url = $logo_url,
            u.tags = $tags,
            u.source = $source,
            u.created_at = datetime(),
            u.updated_at = datetime()
        RETURN u
        """
        result = neo4j_client.execute_write(
            cypher,
            {
                "id": university.id,
                "name": university.name,
                "name_en": university.name_en,
                "location": university.location,
                "country": university.country,
                "ranking": university.ranking,
                "website": university.website,
                "description": university.description,
                "logo_url": university.logo_url,
                "tags": university.tags,
                "source": university.source,
            },
        )
        logger.info(f"Created/updated university: {university.name}")
        return result

    def get_university_alumni(self, university_id: str) -> list[dict]:
        """Get all alumni of a university."""
        cypher = """
        MATCH (p:Person)-[e:STUDIED_AT]->(u:University {id: $university_id})
        RETURN p.name AS name,
               p.id AS person_id,
               e.degree AS degree,
               e.major AS major,
               e.start_date AS start_date,
               e.end_date AS end_date
        ORDER BY e.end_date DESC
        """
        return neo4j_client.execute_query(cypher, {"university_id": university_id})

    # ============================================================
    # Relationships
    # ============================================================

    def add_work_experience(self, exp: WorkExperience) -> dict:
        """Add work experience relationship."""
        cypher = """
        MATCH (p:Person {id: $person_id})
        MATCH (c:Company {id: $company_id})
        MERGE (p)-[r:WORKS_AT {
            position: $position,
            start_date: $start_date
        }]->(c)
        SET r.end_date = $end_date,
            r.is_current = $is_current,
            r.description = $description,
            r.source = $source,
            r.updated_at = datetime()
        RETURN r
        """
        result = neo4j_client.execute_write(
            cypher,
            {
                "person_id": exp.person_id,
                "company_id": exp.company_id,
                "position": exp.position,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "is_current": exp.is_current,
                "description": exp.description,
                "source": exp.source,
            },
        )
        logger.info(f"Added work experience: {exp.person_id} -> {exp.company_id}")
        return result

    def add_education(self, edu: Education) -> dict:
        """Add education relationship."""
        cypher = """
        MATCH (p:Person {id: $person_id})
        MATCH (u:University {id: $university_id})
        MERGE (p)-[e:STUDIED_AT {
            degree: $degree,
            major: $major
        }]->(u)
        SET e.start_date = $start_date,
            e.end_date = $end_date,
            e.description = $description,
            e.source = $source,
            e.updated_at = datetime()
        RETURN e
        """
        result = neo4j_client.execute_write(
            cypher,
            {
                "person_id": edu.person_id,
                "university_id": edu.university_id,
                "degree": edu.degree,
                "major": edu.major,
                "start_date": edu.start_date,
                "end_date": edu.end_date,
                "description": edu.description,
                "source": edu.source,
            },
        )
        logger.info(f"Added education: {edu.person_id} -> {edu.university_id}")
        return result

    def add_person_relation(self, rel: PersonRelation) -> dict:
        """Add person-to-person relationship."""
        cypher = """
        MATCH (p1:Person {id: $person1_id})
        MATCH (p2:Person {id: $person2_id})
        MERGE (p1)-[r:KNOWS {type: $relation_type}]->(p2)
        SET r.description = $description,
            r.start_date = $start_date,
            r.end_date = $end_date,
            r.source = $source,
            r.updated_at = datetime()
        RETURN r
        """
        result = neo4j_client.execute_write(
            cypher,
            {
                "person1_id": rel.person1_id,
                "person2_id": rel.person2_id,
                "relation_type": rel.relation_type,
                "description": rel.description,
                "start_date": rel.start_date,
                "end_date": rel.end_date,
                "source": rel.source,
            },
        )
        logger.info(f"Added relation: {rel.person1_id} -> {rel.person2_id}")
        return result

    # ============================================================
    # Graph Queries
    # ============================================================

    def get_person_network(
        self, person_id: str, depth: int = 2
    ) -> dict:
        """Get person's network (colleagues, classmates, etc.)."""
        cypher = """
        MATCH path = (p:Person {id: $person_id})-[*1..{depth}]-(connected)
        WHERE connected:Person OR connected:Company OR connected:University
        WITH p, connected, length(path) AS distance,
             [r IN relationships(path) | type(r)] AS rel_types
        RETURN DISTINCT
               labels(connected)[0] AS type,
               connected.id AS id,
               connected.name AS name,
               distance,
               rel_types
        ORDER BY distance
        LIMIT 50
        """.format(depth=depth)

        results = neo4j_client.execute_query(cypher, {"person_id": person_id})

        # Build network graph
        nodes = []
        edges = []

        # Add center person
        nodes.append({
            "id": person_id,
            "type": "Person",
            "name": self._get_person_name(person_id),
            "is_center": True,
        })

        for r in results:
            nodes.append({
                "id": r["id"],
                "type": r["type"],
                "name": r["name"],
                "distance": r["distance"],
            })

        return {"nodes": nodes, "edges": edges}

    def get_person_timeline(self, person_id: str) -> list[dict]:
        """Get person's career and education timeline."""
        cypher = """
        MATCH (p:Person {id: $person_id})
        OPTIONAL MATCH (p)-[r:WORKS_AT]->(c:Company)
        OPTIONAL MATCH (p)-[e:STUDIED_AT]->(u:University)
        RETURN collect(DISTINCT {
            type: 'work',
            name: c.name,
            position: r.position,
            start_date: r.start_date,
            end_date: r.end_date,
            is_current: r.is_current
        }) AS work,
        collect(DISTINCT {
            type: 'education',
            name: u.name,
            degree: e.degree,
            major: e.major,
            start_date: e.start_date,
            end_date: e.end_date
        }) AS education
        """
        results = neo4j_client.execute_query(cypher, {"person_id": person_id})

        if not results:
            return []

        # Merge and sort by date
        timeline = []
        for item in results[0]["work"]:
            if item.get("start_date"):
                timeline.append(item)
        for item in results[0]["education"]:
            if item.get("start_date"):
                timeline.append(item)

        timeline.sort(key=lambda x: x.get("start_date", ""), reverse=True)
        return timeline

    def find_connection(
        self, person1_id: str, person2_id: str, max_depth: int = 4
    ) -> list[dict]:
        """Find connection path between two persons."""
        cypher = """
        MATCH path = shortestPath(
            (p1:Person {id: $person1_id})-[*..{max_depth}]-(p2:Person {id: $person2_id})
        )
        RETURN [n IN nodes(path) | {{
            id: n.id,
            name: n.name,
            type: labels(n)[0]
        }}] AS nodes,
        [r IN relationships(path) | {{
            type: type(r),
            properties: properties(r)
        }}] AS relationships,
        length(path) AS hops
        ORDER BY hops
        LIMIT 3
        """.format(max_depth=max_depth)

        return neo4j_client.execute_query(
            cypher,
            {"person1_id": person1_id, "person2_id": person2_id},
        )

    def get_colleagues(
        self, person_id: str, company_id: Optional[str] = None
    ) -> list[dict]:
        """Get colleagues (people who worked at same company)."""
        if company_id:
            cypher = """
            MATCH (p:Person {id: $person_id})-[:WORKS_AT]->(c:Company {id: $company_id})
            MATCH (colleague:Person)-[:WORKS_AT]->(c)
            WHERE colleague.id <> $person_id
            RETURN DISTINCT colleague.id AS id,
                   colleague.name AS name,
                   c.name AS company
            """
        else:
            cypher = """
            MATCH (p:Person {id: $person_id})-[:WORKS_AT]->(c:Company)
            MATCH (colleague:Person)-[:WORKS_AT]->(c)
            WHERE colleague.id <> $person_id
            RETURN DISTINCT colleague.id AS id,
                   colleague.name AS name,
                   c.name AS company
            """

        return neo4j_client.execute_query(
            cypher, {"person_id": person_id, "company_id": company_id}
        )

    def get_classmates(
        self, person_id: str, university_id: Optional[str] = None
    ) -> list[dict]:
        """Get classmates (people who studied at same university)."""
        if university_id:
            cypher = """
            MATCH (p:Person {id: $person_id})-[:STUDIED_AT]->(u:University {id: $university_id})
            MATCH (classmate:Person)-[:STUDIED_AT]->(u)
            WHERE classmate.id <> $person_id
            RETURN DISTINCT classmate.id AS id,
                   classmate.name AS name,
                   u.name AS university
            """
        else:
            cypher = """
            MATCH (p:Person {id: $person_id})-[:STUDIED_AT]->(u:University)
            MATCH (classmate:Person)-[:STUDIED_AT]->(u)
            WHERE classmate.id <> $person_id
            RETURN DISTINCT classmate.id AS id,
                   classmate.name AS name,
                   u.name AS university
            """

        return neo4j_client.execute_query(
            cypher, {"person_id": person_id, "university_id": university_id}
        )

    # ============================================================
    # Statistics
    # ============================================================

    def get_stats(self) -> dict:
        """Get people graph statistics."""
        cypher = """
        MATCH (p:Person) WITH count(p) AS persons
        MATCH (c:Company) WITH persons, count(c) AS companies
        MATCH (u:University) WITH persons, companies, count(u) AS universities
        MATCH ()-[r:WORKS_AT]->() WITH persons, companies, universities, count(r) AS work_rels
        MATCH ()-[r:STUDIED_AT]->() WITH persons, companies, universities, work_rels, count(r) AS edu_rels
        MATCH ()-[r:KNOWS]->() WITH persons, companies, universities, work_rels, edu_rels, count(r) AS know_rels
        RETURN persons, companies, universities, work_rels, edu_rels, know_rels
        """
        results = neo4j_client.execute_query(cypher)
        return results[0] if results else {}

    def _get_person_name(self, person_id: str) -> str:
        """Get person name by ID."""
        cypher = "MATCH (p:Person {id: $id}) RETURN p.name AS name"
        results = neo4j_client.execute_query(cypher, {"id": person_id})
        return results[0]["name"] if results else ""


# Singleton instance
people_manager = PeopleGraphManager()

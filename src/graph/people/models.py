"""People graph data models."""

from dataclasses import dataclass, field


@dataclass
class Person:
    """Person entity."""

    id: str
    name: str
    name_en: str | None = None
    gender: str | None = None
    birth_date: str | None = None
    birth_place: str | None = None
    nationality: str | None = None
    bio: str | None = None
    photo_url: str | None = None
    social_links: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    source: str | None = None
    source_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Company:
    """Company/Organization entity."""

    id: str
    name: str
    name_en: str | None = None
    industry: str | None = None
    size: str | None = None  # startup/small/medium/large/enterprise
    founded: int | None = None
    headquarters: str | None = None
    website: str | None = None
    description: str | None = None
    logo_url: str | None = None
    tags: list[str] = field(default_factory=list)
    source: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class University:
    """University/Educational institution entity."""

    id: str
    name: str
    name_en: str | None = None
    location: str | None = None
    country: str | None = None
    ranking: int | None = None
    website: str | None = None
    description: str | None = None
    logo_url: str | None = None
    tags: list[str] = field(default_factory=list)
    source: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Position:
    """Position/Title entity."""

    id: str
    title: str
    level: str | None = None  # junior/mid/senior/executive/c-suite
    department: str | None = None
    description: str | None = None


@dataclass
class WorkExperience:
    """Work experience relationship."""

    person_id: str
    company_id: str
    position: str
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    description: str | None = None
    source: str | None = None


@dataclass
class Education:
    """Education relationship."""

    person_id: str
    university_id: str
    degree: str | None = None  # bachelor/master/phd/mba
    major: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None
    source: str | None = None


@dataclass
class PersonRelation:
    """Person to person relationship."""

    person1_id: str
    person2_id: str
    relation_type: str  # colleague/classmate/family/friend/mentor
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    source: str | None = None

"""People graph data models."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Person:
    """Person entity."""

    id: str
    name: str
    name_en: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    birth_place: Optional[str] = None
    nationality: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    social_links: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    source: Optional[str] = None
    source_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Company:
    """Company/Organization entity."""

    id: str
    name: str
    name_en: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None  # startup/small/medium/large/enterprise
    founded: Optional[int] = None
    headquarters: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    source: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class University:
    """University/Educational institution entity."""

    id: str
    name: str
    name_en: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    ranking: Optional[int] = None
    website: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    source: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Position:
    """Position/Title entity."""

    id: str
    title: str
    level: Optional[str] = None  # junior/mid/senior/executive/c-suite
    department: Optional[str] = None
    description: Optional[str] = None


@dataclass
class WorkExperience:
    """Work experience relationship."""

    person_id: str
    company_id: str
    position: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None
    source: Optional[str] = None


@dataclass
class Education:
    """Education relationship."""

    person_id: str
    university_id: str
    degree: Optional[str] = None  # bachelor/master/phd/mba
    major: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None


@dataclass
class PersonRelation:
    """Person to person relationship."""

    person1_id: str
    person2_id: str
    relation_type: str  # colleague/classmate/family/friend/mentor
    description: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    source: Optional[str] = None

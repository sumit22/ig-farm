from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://ig_farm:ig_farm_dev@localhost:5432/ig_farm")

engine = create_engine(DATABASE_URL)
Base = declarative_base()


class Capture(Base):
    __tablename__ = "captures"

    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False)
    html = Column(Text, nullable=True)
    title = Column(String(500))
    captured_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    display_name = Column(Text)
    bio = Column(Text)
    followers = Column(Integer, default=0)
    following = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    website = Column(Text)
    is_verified = Column(Boolean, default=False)
    profile_image = Column(Text)
    priority_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    relationships_as_source = relationship(
        "Relationship", foreign_keys="Relationship.source_profile_id", back_populates="source"
    )
    relationships_as_target = relationship(
        "Relationship", foreign_keys="Relationship.target_profile_id", back_populates="target"
    )


class ProfileQueue(Base):
    __tablename__ = "profile_queue"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)
    priority_score = Column(Integer, default=0)
    status = Column(String(20), default="NEW")  # NEW, VISITED, FAILED, SKIPPED
    queued_at = Column(DateTime, default=datetime.utcnow)
    visited_at = Column(DateTime)


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True)
    source_profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    target_profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # SIMILAR, MUTUAL, FOLLOWER, FOLLOWING

    # Relationships
    source = relationship(
        "Profile", foreign_keys=[source_profile_id], back_populates="relationships_as_source"
    )
    target = relationship(
        "Profile", foreign_keys=[target_profile_id], back_populates="relationships_as_target"
    )


def init_db():
    Base.metadata.create_all(bind=engine)

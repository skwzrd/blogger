from datetime import datetime
from enum import Enum
from socket import gethostname

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Table, UniqueConstraint)
from sqlalchemy.orm import DeclarativeBase, registry, relationship

mapper_registry = registry()


class UserRole(Enum):
    admin = 1
    user = 2


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class User(db.Model):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    created_datetime = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_modified_datetime = Column(DateTime(timezone=True), default=datetime.utcnow)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String, unique=True, nullable=False, index=True)
    description = Column(String)
    email = Column(String)
    password = Column(String)
    role = Column(Integer, default=UserRole.user.value)

    posts = relationship("Post", back_populates="user", cascade="all, delete")

    def __unicode__(self):
        return self.username


class Contact(db.Model):
    __tablename__ = "contact"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    message = Column(String, nullable=False)
    created_datetime = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class Log(db.Model):
    __tablename__ = "log"
    id = Column(Integer, primary_key=True, index=True)
    x_forwarded_for = Column(String, index=True)
    remote_addr = Column(String, index=True)
    referrer = Column(String, index=True)
    content_md5 = Column(String)
    origin = Column(String)
    scheme = Column(String)
    method = Column(String)
    path = Column(String, index=True)
    query_string = Column(String)
    duration = Column(Float)
    start_datetime_utc = Column(DateTime(timezone=True))
    end_datetime_utc = Column(DateTime(timezone=True))
    user_agent = Column(String)
    accept = Column(String)
    accept_language = Column(String)
    accept_encoding = Column(String)
    content_length = Column(Integer)


bridge_tag = Table(
    "bridge_tag",
    db.metadata,
    Column("post_id", ForeignKey("post.id"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
    UniqueConstraint("post_id", "tag_id"),
)


class BridgeTag:
    pass


mapper_registry.map_imperatively(BridgeTag, bridge_tag)


class File(db.Model):
    __tablename__ = "file"

    id = Column(Integer, primary_key=True, index=True)
    server = Column(String, server_default=gethostname())
    relative_path = Column(String)
    server_file_name = Column(String, unique=True)
    file_name = Column(String)
    file_type = Column(String)
    upload_date = Column(DateTime(), default=datetime.utcnow)

    post_id = Column(Integer, ForeignKey("post.id"), nullable=False)
    post = relationship("Post", back_populates="files")

    def __unicode__(self):
        return self.file_name


class Tag(db.Model):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, unique=True)

    posts = relationship("Post", back_populates="tags", secondary=bridge_tag)

    def __unicode__(self):
        return self.text


class Post(db.Model):
    """
    - The Post-User    relationship is many-to-one.
    - The Post-File    relationship is one-to-many.
    - The Post-Tag     relationship is many-to-many.
    - The Post-Comment relationship is one-to-many.
    """

    __tablename__ = "post"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    text = Column(String)
    published_date = Column(DateTime(), default=datetime.utcnow)
    last_modified_date = Column(DateTime(), default=datetime.utcnow)
    is_published = Column(Boolean, default=True)

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="posts")

    comments = relationship("Comment", back_populates="post", cascade="all, delete")

    files = relationship("File", back_populates="post", cascade="all, delete")

    tags = relationship("Tag", back_populates="posts", secondary=bridge_tag)

    def __unicode__(self):
        return self.title


class Comment(db.Model):
    __tablename__ = "comment"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    text = Column(String)
    published_date = Column(DateTime(timezone=True), default=datetime.utcnow)

    post_id = Column(Integer, ForeignKey("post.id"), nullable=False)
    post = relationship("Post", back_populates="comments")

    def __unicode__(self):
        return self.title

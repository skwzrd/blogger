from socket import gethostname

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (Boolean, Column, Date, DateTime, ForeignKey, Integer,
                        String, Table, UniqueConstraint)
from sqlalchemy.orm import DeclarativeBase, registry, relationship
from sqlalchemy.sql import func

mapper_registry = registry()

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class User(db.Model):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String, unique=True)
    description = Column(String)
    email = Column(String)
    password = Column(String)

    posts = relationship("Post", back_populates="user")

    def __unicode__(self):
        return self.username


bridge_file = Table(
    "bridge_file",
    db.metadata,
    Column("id", Integer, autoincrement=True, index=True),
    Column("post_id", ForeignKey("post.id"), primary_key=True),
    Column("file_id", ForeignKey("file.id"), primary_key=True),
    UniqueConstraint("post_id", "file_id"),
)


class BridgeFile:
    pass


mapper_registry.map_imperatively(BridgeFile, bridge_file)

bridge_tag = Table(
    "bridge_tag",
    db.metadata,
    Column("id", Integer, autoincrement=True, index=True),
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
    file_path = Column(String, unique=True)
    file_name = Column(String)
    file_type = Column(String)
    upload_date = Column(Date(), server_default=func.current_date())

    def __unicode__(self):
        return self.file_name


class Tag(db.Model):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, unique=True)

    def __unicode__(self):
        return self.text


class Post(db.Model):
    """
    - The Post-File    relationship is many-to-many.
    - The Post-Tag     relationship is many-to-many.
    - The Post-Comment relationship is one-to-many.
    - The Post-User    relationship is one-to-one.
    """

    __tablename__ = "post"

    id = Column(Integer, primary_key=True, index=True)
    files = relationship("File", secondary=bridge_file, backref="post")
    tags = relationship("Tag", secondary=bridge_tag, backref="post")
    text = Column(String)
    title = Column(String)
    published_date = Column(Date(), server_default=func.current_date())
    last_modified_date = Column(Date(), server_default=func.current_date())
    is_published = Column(Boolean)

    user_id = Column(ForeignKey("user.id"))
    user = relationship("User", back_populates="posts")

    comments = relationship("Comment", back_populates="post")

    def __unicode__(self):
        return self.title


class Comment(db.Model):
    __tablename__ = "comment"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    text = Column(String)
    published_date = Column(DateTime(timezone=True), server_default=func.now())

    post_id = Column(ForeignKey("post.id"))
    post = relationship("Post", back_populates="comments")

    def __unicode__(self):
        return self.title

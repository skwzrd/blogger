from sqlalchemy import select

from models import BridgeFile, BridgeTag, File, Post, Tag, User, db


def get_user_by_username(username):
    return db.session.scalar(select(User).where(User.username == username))


def get_user_by_id(user_id):
    return db.session.scalar(select(User).where(User.id == user_id))


def get_post_by_id(post_id):
    result = db.session.scalar(
        select(Post, Tag, File)
        .join(BridgeTag, Post.id == BridgeTag.post_id, isouter=True)
        .join(Tag, Tag.id == BridgeTag.tag_id, isouter=True)
        .join(BridgeFile, Post.id == BridgeFile.post_id, isouter=True)
        .join(File, File.id == BridgeFile.file_id, isouter=True)
        .where(Post.id == post_id)
    )
    return result


def get_published_post_by_id(post_id):
    result = db.session.scalar(
        select(Post, Tag, File)
        .join(BridgeTag, Post.id == BridgeTag.post_id, isouter=True)
        .join(Tag, Tag.id == BridgeTag.tag_id, isouter=True)
        .join(BridgeFile, Post.id == BridgeFile.post_id, isouter=True)
        .join(File, File.id == BridgeFile.file_id, isouter=True)
        .where(Post.id == post_id)
        .where(Post.is_published == True)
    )
    return result


def get_posts_by_tag_id(tag_id):
    result = db.session.scalars(
        select(Post)
        .join(BridgeTag, Post.id == BridgeTag.post_id)
        .join(Tag, Tag.id == BridgeTag.tag_id)
        .where(Tag.id == tag_id)
    )
    return result


def get_published_posts_by_tag_id(tag_id):
    result = db.session.scalars(
        select(Post)
        .join(BridgeTag, Post.id == BridgeTag.post_id)
        .join(Tag, Tag.id == BridgeTag.tag_id)
        .where(Tag.id == tag_id)
        .where(Post.is_published == True)
    )
    return result
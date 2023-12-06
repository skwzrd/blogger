from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

from configs import CONSTS
from models import Comment, Contact, File, Post, Tag, User, UserRole, db


def build_db():
    """Init and testing, together."""

    engine = create_engine(CONSTS.SQLALCHEMY_DATABASE_URI)
    db.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.commit()

    admin1 = User(
        first_name="admin",
        last_name="admin",
        username=CONSTS.admin_username,
        description="admin",
        email=CONSTS.admin_username,
        password=generate_password_hash(CONSTS.admin_password),
        role=UserRole.admin.value,
    )

    comment1 = Comment(title="title1", text="text1")
    file1 = File(file_path="/123.txt", file_name="123.txt")
    tag1 = Tag(text="tag1")
    tag2 = Tag(text="tag2")

    post1 = Post(title="title1", text="text1", is_published=True, user=admin1, comments=[comment1], files=[file1], tags=[tag1, tag2])
    post1.comments = [comment1]

    contact1 = Contact(
        name="name1",
        email="email1",
        message="message1",
    )

    session.add_all([admin1, contact1, post1])
    session.commit()

    posts = session.scalars(select(Post)).all()
    post = posts[0]

    assert len(posts) == 1
    assert post.id == post1.id
    assert post.user.username == CONSTS.admin_username
    assert post.comments[0].text == comment1.text
    assert post.files[0].file_path == file1.file_path
    assert len(post.comments) == 1
    assert len(post.files) == 1
    assert len(post.tags) == 2

    contact_name = session.scalar(select(Contact.name))
    assert contact_name == contact1.name

    # delete everything except for admin user
    session.delete(contact1)
    session.delete(post)
    session.delete(tag1)  # cascade deletions do not apply to tags
    session.delete(tag2)
    session.commit()

    posts = session.scalars(select(Post)).all()
    assert len(posts) == 0


if __name__ == "__main__":
    build_db()

from sqlalchemy import create_engine, delete, select, update
from sqlalchemy.orm import Session

from models import Comment, File, Post, Tag, User, db

print('Running model tests...')


engine = create_engine("sqlite://", echo=False)
db.metadata.create_all(engine)

with Session(engine) as session:
    # insert
    u = User(username="spongebob", first_name='spongebob', last_name='squarepants', description='admin', email='idk', password=None)
    
    p = Post(
        text="Hey, Patrick!",
        tags=[Tag(text="cartoon"), Tag(text="I'm ready")],
        user=u,
        comments=[Comment(title='Is this the Krusty Krab?'), Comment(text='Hello?'), Comment(text='Sea')],
        files=[File(server='main', file_path='/path/to/file', file_name='image.png', file_type='png', title='bikini-bottom')]
    )

    t = Tag(text='ocean')

    session.add_all([u, p, t])
    session.commit()

    t = Tag(text='beach')
    session.add(t)
    session.commit()

    # select
    sql_string = select(Tag.text).where(Tag.text.contains('ocean'))
    r = session.scalar(sql_string)
    assert r == 'ocean', r

    sql_string = select(Tag).where(Tag.text.contains('ocean'))
    r = session.scalar(sql_string)
    assert r.text == 'ocean', r

    sql_string = select(Tag).where(Tag.text.contains('ocean'))
    r = session.scalar(sql_string)
    assert r.text == 'ocean', r

    sql_string = select(Post).join(Comment).where(Comment.text.in_(['', 'Sandy']))
    r = session.scalar(sql_string)
    assert r == None, r

    sql_string = select(Post, Comment).join(Comment).where(Comment.text.in_(['', 'Sandy', 'Hello?']))
    all_ = session.execute(sql_string).all()[0]
    first = session.execute(sql_string).first()
    assert all_ == first
    assert first[0].text == 'Hey, Patrick!' and first[1].text == 'Hello?', r

    sql_string = select(User.first_name).join(Post).join(Comment).where(Comment.text == "Sea")
    r = session.scalar(sql_string)
    assert r == 'spongebob', r

    # update
    sql_string = update(User).where(User.first_name == 'spongebob').values(first_name='Sponge')
    r = session.execute(sql_string)
    session.commit()

    sql_string = select(User.first_name).where(User.first_name == 'spongebob')
    r = session.scalar(sql_string)
    assert r is None, r
    
    sql_string = select(User.first_name).where(User.first_name == 'Sponge')
    r = session.scalar(sql_string)
    assert r is not None, r

    # delete
    sql_string = delete(User).where(User.first_name == 'Sponge')
    r = session.execute(sql_string)
    session.commit()

    sql_string = select(User.first_name).where(User.first_name == 'Sponge')
    r = session.scalar(sql_string)
    assert r is None, r

    sql_string = select(User.first_name).where(User.first_name == 'Sponge')
    r = session.scalar(sql_string)
    assert r is None, r

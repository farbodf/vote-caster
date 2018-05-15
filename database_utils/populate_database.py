from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_utils.database_setup import Category, Poll, Choice, Base

engine = create_engine('sqlite:///votes.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def add_and_commit(item, session):
    session.add(item)
    session.commit()


# Add a few categories
technology_category = Category(name="Technology")
add_and_commit(technology_category, session)

music_category = Category(name="Music")
add_and_commit(music_category, session)

general_category = Category(name="General")
add_and_commit(general_category, session)

# Add a few polls
music_poll = Poll(
    title="Pop vs Rock",
    description="Which one is your favorite?",
    category=music_category
)
add_and_commit(music_poll, session)

tech_poll = Poll(
    title="Favorite operating system?",
    category=technology_category
)
add_and_commit(tech_poll, session)

# Add choices
add_and_commit(Choice(name="MacOS", poll=tech_poll), session)
add_and_commit(Choice(name="Windows", poll=tech_poll), session)
add_and_commit(Choice(name="Linux", poll=tech_poll), session)
add_and_commit(Choice(name="Rock", poll=music_poll), session)
add_and_commit(Choice(name="Pop", poll=music_poll), session)

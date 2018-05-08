from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    def __repr__(self):
        return "<Category(name='{}', description='{}')>".format(
            self.name, self.description
        )


class Poll(Base):
    __tablename__ = 'poll'
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    description = Column(Text)
    up_vote = Column(Integer, default=0, nullable=False)
    down_vote = Column(Integer, default=0, nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)

    def __repr__(self):
        return "<Poll(title='{}', description='{}'," \
               " upvotes='{}', downvotes='{}')>".format(
            self.title, self.description, self.up_vote, self.down_vote
        )


class Choice(Base):
    __tablename__ = 'choice'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    count = Column(Integer, default=0, nullable=False)
    poll_id = Column(Integer, ForeignKey('poll.id'))
    poll = relationship(Poll)


engine = create_engine('sqlite:///votes.db', echo=True)
Base.metadata.create_all(engine)

from flask import Flask, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_utils.database_setup import Base, Poll, Choice

app = Flask(__name__)

engine = create_engine('sqlite:///votes.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# @app.route('/')
@app.route('/hello')
def HelloWorld():
    return "Hello World"

@app.route('/')
@app.route('/polls')
def polls():
    polls = session.query(Poll).all()
    choices = session.query(Choice).all()
    return render_template('polls.html', polls=polls, choices=choices)


@app.route('/polls/<int:poll_id>')
def show_poll(poll_id):
    return "Show specific poll"


@app.route('/polls/add', methods=['GET', 'POST'])
def create_poll():
    return "page to create a new poll"


@app.route('/polls/<int:poll_id>/edit', methods=['GET', 'POST'])
def edit_poll(poll_id):
    return "page to edit a poll."


@app.route('/polls/<int:poll_id>/delete', methods=['GET', 'POST'])
def delete_poll(poll_id):
    return "page to delete a poll."




if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8081)

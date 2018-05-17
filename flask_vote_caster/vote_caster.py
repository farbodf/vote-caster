from flask import Flask, render_template, request, redirect, url_for
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_utils.database_setup import Base, Poll, Choice, Category

app = Flask(__name__)

engine = create_engine('sqlite:///votes.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/polls')
def polls():
    polls = session.query(Poll).all()
    choices = session.query(Choice).all()
    return render_template('polls.html', polls=polls, choices=choices)


@app.route('/polls/<int:poll_id>', methods=['GET', 'POST'])
def show_poll(poll_id):
    if request.method == 'GET':
        choices = session.query(Choice).filter_by(poll_id=poll_id).all()
        poll = session.query(Poll).filter_by(id=poll_id).one()
        return render_template(
            'show_poll.html',
            poll=poll,
            choices=choices
        )


@app.route('/polls/add', methods=['GET', 'POST'])
def create_poll():
    if request.method == 'POST':
        category = session.query(Category).filter_by(name='General').one()

        new_poll = Poll(
            title=request.form['title'],
            description=request.form['description'],
            category=category
        )

        session.add(new_poll)
        session.commit()

        choices = [
            choice.strip() for choice in request.form['choices'].split(",")
        ]

        for choice in choices:
            session.add(
                Choice(name=choice, poll=new_poll)
            )
            session.commit()

        return redirect(url_for('show_poll', poll_id=new_poll.id))

    if request.method == 'GET':
        return render_template('create_poll.html')


@app.route('/polls/<int:poll_id>/edit', methods=['GET', 'POST'])
def edit_poll(poll_id):
    return "page to edit a poll."


@app.route('/polls/<int:poll_id>/delete', methods=['GET', 'POST'])
def delete_poll(poll_id):
    return "page to delete a poll."


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8081)

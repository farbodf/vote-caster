import random
import string
import yaml
import json
import httplib2
import requests
import logging
from flask import (
    Flask, render_template, request, redirect, url_for, make_response, flash)
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
from flask import make_response

from database_utils.database_setup import Base, Poll, Choice, Category


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("flask_vote_caster")

app = Flask(__name__)

engine = create_engine('sqlite:///votes.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

with open("params.yaml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)


@app.route('/login')
def show_login():
    state = ''.join(random.choice(string.ascii_uppercase +
                                  string.ascii_lowercase +
                                  string.digits) for x in range(32))
    login_session['state'] = state
    return render_template(
        'login.html',
        data_clientid=cfg['keys']['google_data_clientid'],
        STATE=state
    )

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        LOGGER.info("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    LOGGER.info('data is: %s', data)
    flash("you are now logged in as {}".format(login_session['username']))
    return render_template(
        'logged_in.html',
        username=login_session['username'],
        picture=login_session['picture']
    )


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        LOGGER.info('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    LOGGER.info('In gdisconnect access token is %s', access_token)
    LOGGER.info('login session is: %s', login_session)
    LOGGER.info('User name is: %s', login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token={}'.format(
        login_session['access_token']
    )
    LOGGER.info('url is %s', url)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    LOGGER.info('result is %s', result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

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
    app.secret_key = 'Secret Key'
    app.debug = True
    app.run(host='0.0.0.0', port=8081)

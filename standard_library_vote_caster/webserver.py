import cgi
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_utils.database_setup import Base, Poll, Category, Choice

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(name='http_server')

# Setup connection to database
engine = create_engine("sqlite:///votes.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


def add_and_commit(item, session):
    session.add(item)
    session.commit()


class WebServerHandler(BaseHTTPRequestHandler):
    def create_new_poll_get(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        message = "<html><body>"
        message += """
                        <form action="/polls/new" method="post" enctype="multipart/form-data">
                            Poll title: <input type="text" name="poll_name"><br>
                            Description: <input type="text" name="description"><br>
                            Choices (comma separated): <input type="text" name="choices"><br> 
                            <input type="submit" value="Submit">
                        </form> 
                        """
        message += "</body></html>"
        self.wfile.write(message.encode())
        LOGGER.info(message)

    def show_polls_get(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        message = """
        <html><body>
        <p><a href='/polls/new'>Add a new poll</a></p>
        """
        polls = session.query(Poll).all()
        for poll in polls:
            message += "<p><a href='/polls/{}/poll'>{}</a><br>{}<br>".format(
                poll.id,
                poll.title,
                poll.description
            )
            choices = session.query(Choice).filter_by(poll_id=poll.id)
            for choice in choices:
                message += """
                    <form action="/polls/{}/{}/choice" method="post" enctype="multipart/form-data"> 
                    <input type="submit" value="{}: {}">
                    </form>
                    """.format(
                    poll.id,
                    choice.id,
                    choice.name,
                    choice.count
                )
            message += "<a href='/polls/{}/edit'>Edit</a>".format(poll.id)
            message += ", <a href='/polls/{}/delete'>Delete</a>".format(poll.id)
            message += "</p>"
        message += "</body></html>"
        self.wfile.write(message.encode())
        LOGGER.info(message)

    def show_poll_get(self):
        LOGGER.info("HERE")
        poll_id = self.path.split("/")[-2]
        poll = session.query(Poll).filter_by(id=poll_id).one()
        if poll:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            choices = session.query(Choice).filter_by(poll_id=poll_id).all()
            message = f"""
            <html><body>
                <h2>{poll.title}</h2>
                <p>{poll.description}</p>
                <p>
            """
            for choice in choices:
                message += """
                    <form action="/poll/{}/{}/choice" method="post" enctype="multipart/form-data"> 
                    <input type="submit" value="{}: {}">
                    </form>
                    """.format(
                    poll_id,
                    choice.id,
                    choice.name,
                    choice.count
                )
            message += "</p><a href='/polls/{}/edit'>Edit</a>".format(poll.id)
            message += ", <a href='/polls/{}/delete'>Delete</a>".format(poll.id)
        message += "</body></html>"
        self.wfile.write(message.encode())


    def create_new_poll_post(self):
        ctype, pdict = cgi.parse_header(
            self.headers.get('Content-type'))
        pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')
        if ctype == 'multipart/form-data':
            fields = cgi.parse_multipart(self.rfile, pdict)
            poll_name = fields.get('poll_name')[0].decode()
            poll_description = fields.get('description')[0].decode()
            choices = fields.get('choices')[0].decode()
        LOGGER.info(poll_name)
        category = session.query(Category).filter_by(
            name='General').one()
        poll = Poll(title=poll_name,
                    description=poll_description,
                    category=category)
        add_and_commit(poll, session)
        for choice in choices.split(','):
            add_and_commit(Choice(name=choice.strip(), poll=poll),
                           session)
        self.send_response(301)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', '/polls')
        self.end_headers()

    def poll_vote_post(self):
        poll_id = self.path.split("/")[-3]
        choice_id = self.path.split("/")[-2]
        choice = session.query(Choice).filter_by(id=choice_id).one()
        if choice:
            choice.count += 1
            add_and_commit(choice, session)
            self.send_response(301)
            self.send_header('Content-type', 'text/html')
            if 'polls' in self.path:
                self.send_header('Location', '/polls')
            else:
                self.send_header('Location', f'/{poll_id}/poll')
            self.end_headers()

    def edit_poll_post(self):
        poll_id = self.path.split('/')[-2]
        poll = session.query(Poll).filter_by(id=poll_id).one()
        if poll:
            ctype, pdict = cgi.parse_header(
                self.headers.get('Content-type')
            )
            pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                poll_name = fields.get('poll_name')[0].decode()
                description = fields.get('description')[0].decode()
                if poll_name:
                    poll.title = poll_name
                    add_and_commit(poll, session)
                if description:
                    poll.description = description
                    add_and_commit(poll, session)
                choices = session.query(Choice).filter_by(poll_id=poll_id).all()
                for choice in choices:
                    name = fields.get(str(choice.id))[0].decode()
                    if name:
                        choice.name = name
                        add_and_commit(choice, session)
                new_choices = fields.get('choices')[0].decode()
                if new_choices:
                    choices = [c.strip() for c in new_choices.split(",")]
                    for choice in choices:
                        add_and_commit(Choice(name=choice, poll=poll))
            self.send_response(301)
            self.send_header('Content-type', 'text/html')
            self.send_header('Location', '/polls')
            self.end_headers()

    def delete_poll_post(self):
        poll_id = self.path.split("/")[-2]
        poll = session.query(Poll).filter_by(id=poll_id).one()
        if poll:
            choices = session.query(Choice).filter_by(poll_id=poll.id).all()
            for choice in choices:
                session.delete(choice)
                session.commit()
            session.delete(poll)
            session.commit()
            self.send_response(301)
            self.send_header('Content-type', 'text/html')
            self.send_header('Location', '/polls')
            self.end_headers()

    def edit_poll_get(self):
        poll_id = self.path.split("/")[-2]
        poll = session.query(Poll).filter_by(id=poll_id).one()
        if poll:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            message = "<html><body>"
            message += f"""
            <h2>Edit</h2>
                <form action="/polls/{poll_id}/edit" method="post" enctype="multipart/form-data">
                    Poll title: <input type="text" name="poll_name" placeholder="{poll.title}"><br>
                    Description: <input type="text" name="description" placeholder="{poll.description}"><br>
                    Choices: <br>
                    """
            choices = session.query(Choice).filter_by(poll_id=poll.id).all()
            for choice in choices:
                message += f"""
                <input type="text" name="{choice.id}" placeholder="{choice.name}">
                """
            message += """
            <br>
            Add more choices (comma separated): <input type="text" name="choices"><br>
                    <input type="submit" value="Confirm">
                </form>
            </body></html>
            """
            self.wfile.write(message.encode())
            LOGGER.info(message)

    def delete_poll_get(self):
        poll_id = self.path.split("/")[-2]
        poll = session.query(Poll).filter_by(id=poll_id).one()
        if poll:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            message = "<html><body>"
            message += f"""
                <h2>Delete</h2>
                <p>Are you sure you want to delete poll '{poll.title}'?</p>
                <form action="/polls/{poll_id}/delete" method="post" enctype="multipart/form-data">
                <input type="submit" value="Delete">
                </form> 
                </body></html>
                """
            self.wfile.write(message.encode())
            LOGGER.info(message)

    def do_GET(self):
        try:
            if self.path.endswith("/polls") or self.path == "/":
                self.show_polls_get()

            if self.path.endswith("/poll"):
                self.show_poll_get()

            if self.path.endswith("/polls/new"):
                self.create_new_poll_get()

            if self.path.endswith("/edit"):
                self.edit_poll_get()

            if self.path.endswith("/delete"):
                self.delete_poll_get()

        except IOError:
            self.send_error(404, 'File not found {}'.format(self.path))

    def do_POST(self):
        try:
            if self.path.endswith("polls/new"):
                self.create_new_poll_post()

            if self.path.endswith("/edit"):
                self.edit_poll_post()

            if self.path.endswith("/delete"):
                self.delete_poll_post()

            if self.path.endswith("/choice"):
                self.poll_vote_post()

        except IOError:
            self.send_error(404, 'File not found {}'.format(self.path))


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), WebServerHandler)
        LOGGER.info("Server running on port: {}".format(port))
        server.serve_forever()

    except KeyboardInterrupt:
        LOGGER.info("Interruped, stopping the server")
        server.socket.close()


if __name__ == "__main__":
    main()

import logging
import cgi
from http.server import BaseHTTPRequestHandler, HTTPServer
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from database_setup import Base, Poll, Category, Choice

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
    def do_GET(self):
        try:
            if self.path.endswith("/polls"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                message = "<html><body>"
                polls = session.query(Poll).all()
                for poll in polls:
                    message += "<p>{}<br>{}<br>".format(poll.title,
                                                        poll.description)
                    choices = session.query(Choice).filter_by(poll_id=poll.id)
                    for choice in choices:
                        message += "<a href="">{}</a><br>".format(choice.name)
                    message += "<br><a href="">Edit</a>, <a href="">Delete</a>"
                    message += "</p>"
                message += "</body></html>"
                self.wfile.write(message.encode())
                LOGGER.info(message)

            if self.path.endswith("/polls/new"):
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
        except IOError:
            self.send_error(404, 'File not found {}'.format(self.path))

    def do_POST(self):
        try:
            if self.path.endswith("polls/new"):
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

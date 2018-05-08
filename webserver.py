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

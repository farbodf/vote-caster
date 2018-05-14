# Vote Caster

A Simple web service (with no fancy frontend, only basic HTML tags) demonstrating the Python's standard http.server package capability. 

By running the webserver and visiting localhost on port 8080 (you can change these in the code), you view polls, create new polls, edit them, delete them, and of course vote for the choices there.

This project uses SQLAlchemy as an ORM to communicate with the database. It uses MySQL for the database.

## How to run

You can first run the ``database_setup.py`` script to setup the database. Running the script will create the votes.db

Afterwards it's possilbe to run the ``populate_database.py`` to inject dummy data into the database (Two sample polls).

Finally, you can run the ``webserver.py`` and visit the localhost on port 8080 to check the project and start either voting or editing polls :)
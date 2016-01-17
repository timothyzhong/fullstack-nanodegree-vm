Environment:
SQLAlchemy, Python, Flask

How to use:
1. Setup the database with schema.
   python catalog/database_setup.py
2. Insert initial data into the database.
   python catalog/addItems.py
3. Start the server.
   python runserver.py
4. Access the application through browser with url localhost:8000/catalog

User can browse items in different categories. Each item has a name, a
paragraph of description, an optional image and belongs to one of the
existed categories When logged in with Google or Facebook account, user
can add new item to categories. A user can also edit or delete
items that he/she created.

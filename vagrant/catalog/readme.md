Environment:
SQLAlchemy, Python, Flask

How to use:
Please do steps 1~3 in /vagrant/catalog directory, otherwise the database
 can't setup correctly.

1. Setup the database with schema.
   python catalog/database_setup.py

2. Insert initial data into the database.
   python catalog/addItems.py

3. Start the server.
   python runserver.py

4. Access the application through browser

   Public pages:
   Index page: http://localhost:8000/catalog
   User login page: http://localhost:8000/login
   JSON API: http://localhost:8000/catalog.json
   View items of a category: http://localhost:8000/catalog/<category name>/items
   View detail of an item: http://localhost:8000/catalog/<category name>/<item name>

   User need to be logged in to access:
   Add new item: http://localhost:8000/catalog/new

   Only the user who created that item can access:
   Edit an item: http://localhost:8000/catalog/<category name>/<item name>/edit
   Delete an item: http://localhost:8000/catalog/category name/<item name>/delete

User can browse items in different categories. Each item has a name, a
paragraph of description, an optional image and belongs to one of the
existed categories When logged in with Google or Facebook account, user
can add new item to categories. A user can also edit or delete
items that he/she created.

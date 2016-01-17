# Insert initial data into database
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item
DIR = "/vagrant/catalog/catalog/static/images"

engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

# delete old data
session.query(Item).delete()
session.query(Category).delete()
session.query(User).delete()
session.commit()

# add new data
cats = []

user1 = User(name="Tim", email="timothy7784@gmail.com", picture="")

cat1 = Category(name="Basketball", user=user1)
cats.append(cat1)

item1 = Item(name="Ball", description="The ball", image=None,
             category=cat1, user=user1)
item2 = Item(name="Basket", description="The target basket",
             image=None, category=cat1, user=user1)

cat2 = Category(name="Skating", user=user1)
cats.append(cat2)

item3 = Item(name="Skateboard", description="Skateboard",
             image=None, category=cat2, user=user1)

cats.append(Category(name="Football", user=user1))
cats.append(Category(name="Tennis", user=user1))
cats.append(Category(name="Skiing", user=user1))
cats.append(Category(name="Running", user=user1))
cats.append(Category(name="Baseball", user=user1))


session.add(user1)
for cat in cats:
    session.add(cat)

    # create directories for each category
    directory = DIR + '/' + cat.name
    if not os.path.exists(directory):
        os.makedirs(directory)

session.add(item1)
session.add(item2)
session.add(item3)
# Save to database
session.commit()


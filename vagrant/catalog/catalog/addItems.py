from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item


engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

# delete old data
session.query(Item).delete()
session.query(Category).delete()
session.commit()


# add new data
cat1 = Category(name="Basketball")
item1 = Item(name="Ball", category=cat1)
item2 = Item(name="Basket", category=cat1)

cat2 = Category(name="Skating")
item3 = Item(name="Skate", category=cat2)
item4 = Item(name="Stick", category=cat2)

session.add(cat1)
session.add(cat2)
session.add(item1)
session.add(item2)
session.add(item3)
session.add(item4)

session.commit()

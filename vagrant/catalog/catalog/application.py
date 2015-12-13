from catalog import app
from flask import render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from catalog.database_setup import Base, Category, Item

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
@app.route('/catalog')
def index():
    category_list = session.query(Category).all()
    print "show list %s" % len(category_list)
    for cat in category_list:
        print cat.name
    return render_template('main.html', category_list = category_list)

@app.route('/catalog/<category_name>/items')
def itemsOfCategory(category_name):
    print "looking up items of %s" % category_name
    cat = session.query(Category).filter_by(name=category_name).one()
    print "cat_id is %s" % cat.id
    item_list = session.query(Item).filter_by(category_id=cat.id).all()
    for item in item_list:
        print "%s of %s" % (item.name, item.category_id)
    return render_template('itemsOfCategory.html', items = item_list, category_name = category_name)

@app.route('/catalog/<category_name>/<item_name>')
def item(category_name, item_name):
    return render_template('item.html', category_name = category_name, item_name = item_name)


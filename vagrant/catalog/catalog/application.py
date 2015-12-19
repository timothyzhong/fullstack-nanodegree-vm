from catalog import app
from flask import render_template, jsonify, json, request, flash
from flask import session as login_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from catalog.database_setup import Base, Category, Item

# imports for login
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('catalog/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

# setup for using database
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
    return render_template('main.html', category_list=category_list)


@app.route('/catalog/<category_name>/items')
def itemsOfCategory(category_name):
    print "looking up items of %s" % category_name
    cat = session.query(Category).filter_by(name=category_name).one()
    print "cat_id is %s" % cat.id
    item_list = session.query(Item).filter_by(category_id=cat.id).all()
    for item in item_list:
        print "%s of %s" % (item.name, item.category_id)
    return render_template('itemsOfCategory.html', items=item_list,
                           category_name=category_name)


@app.route('/catalog/<category_name>/<item_name>')
def item(category_name, item_name):
    cat = session.query(Category).filter_by(name=category_name).one()
    items = session.query(Item).filter_by(category_id=cat.id,
                                          name=item_name).all()
    return render_template('item.html', category_name=category_name,
                           items=items)


@app.route('/catalog.json')
def catalogJSON():
    cat_list = session.query(Category).all()
    result = []
    for cat in cat_list:
        items = session.query(Item).filter_by(category_id=cat.id).all()
        catObj = dict(id=cat.id, name=cat.name,
                      item=[i.serialize for i in items])
        result.append(catObj)
    return jsonify(Category=result)


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# Handle Google API
@app.route('/gconnect', methods=['POST'])
def gconnect():
    print "gconnect"

    print login_session['state']
    print request.args.get('state')

    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        print "Invalid state parameter."
        return response

    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('catalog/client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        print "Failed to upgrade the authorization code."
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

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        print "Token's user ID doesn't match given user ID."
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        print "Token's client ID does not match app's."
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        print 'Current user is already connected.'
        return response

    # Store the access token in the session for later use.
    # login_session['credentials'] = credentials
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

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output
# Server application
import os
import time
from catalog import app
from flask import render_template, jsonify, json, request, redirect, url_for
from flask import session as login_session
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from catalog.database_setup import Base, User, Category, Item
from werkzeug import secure_filename

# imports for login
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response, flash
import requests
from functools import wraps

# Application setup
CLIENT_ID = json.loads(
    open('catalog/client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"
UPLOAD_FOLDER = '/vagrant/catalog/catalog/static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# setup for using database
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# setup for file upload
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


# Login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# User Helper Functions
def createUser(login_session):
    """Create user entry in database"""
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    """Get the user from database using their user id"""
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    """Get user id from database using their email address"""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# file upload functions
def allowed_file(filename):
    """Check whether a file name is legal"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/catalog/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle upload requests"""
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect('/catalog')
    return '''
        <!doctype html>
        <title>Upload new File</title>
        <h1>Upload new File</h1>
        <form action="" method=post enctype=multipart/form-data>
          <p><input type=file name=file>
             <input type=submit value=Upload>
        </form>
        '''


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    """Return login page"""
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/')
@app.route('/catalog')
@app.route('/catalog/')
def index():
    """Return index page"""
    item_list = session.query(Item).order_by(Item.id.desc()).all()
    if len(item_list) > 4:
        del item_list[5:]
    category_list = session.query(Category).order_by(Category.name).all()
    if 'username' not in login_session:
        return render_template('publicIndex.html',
                               category_list=category_list,
                               items=item_list)
    else:
        return render_template('index.html', category_list=category_list,
                               items=item_list)


@app.route('/catalog/<category_name>/items')
def itemsOfCategory(category_name):
    """Return category page with all its items"""
    print "looking up items of %s" % category_name
    cat = session.query(Category).filter_by(name=category_name).one()
    print "cat_id is %s" % cat.id
    item_list = session.query(Item).filter_by(category_id=cat.id).all()
    category_list = session.query(Category).order_by(Category.name).all()
    for item in item_list:
        print "%s of %s" % (item.name, item.category_id)
    return render_template('itemsOfCategory.html', items=item_list,
                           category_name=category_name,
                           category_list=category_list)


@app.route('/catalog/<category_name>/<item_name>')
def item(category_name, item_name):
    """Return detailed item page"""
    cat = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(category_id=cat.id,
                                         name=item_name).one()
    creator = getUserInfo(item.user_id)

    # check whether user is logged in
    if 'username' not in login_session or \
       creator.id != item.user_id:            # current user is not the creator
        return render_template('publicitem.html',
                               category_name=category_name,
                               item=item)
    else:
        return render_template('item.html', category_name=category_name,
                               item=item)


@app.route('/catalog/new', methods=['GET', 'POST'])
@login_required
def newItem():
    """Create new item"""

    category_list = session.query(Category).order_by(Category.name).all()
    if request.method == 'POST':
        itemName = request.form['name']

        # check for empty name
        if not itemName or itemName == '':
            flash('Please enter an item name')
            time.sleep(1)
            return render_template('newItem.html', category_list=category_list)

        # check for duplicate item
        cat = session.query(Category).filter_by(name=request.form['category']).one()
        item = session.query(Item).filter_by(name=itemName, category=cat).all()
        if item:
            flash('Item %s of %s already existed' % (item[0].name, cat.name))
            time.sleep(1)
            return render_template('newItem.html', category_list=category_list)

        # save upload file
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = itemName + '.' + file.filename.rsplit('.', 1)[1]
            filename = secure_filename(filename)
            filedir = cat.name + "/" + filename
            finalDir = os.path.join(app.config['UPLOAD_FOLDER'], filedir)
            try:
                file.save(finalDir)
            except IOError:
                print IOError
                flash('Failed to save image file')

        # create new item
        user = session.query(User).filter_by(id=login_session['user_id']).one()
        newItem = Item(name=itemName,
                       description=request.form['description'],
                       category=cat,
                       user=user,
                       image=filedir)
        session.add(newItem)
        flash('New item %s created' % newItem.name)
        session.commit()

        return redirect('/catalog')
    # get method
    else:
        return render_template('newItem.html', category_list=category_list)


@app.route('/catalog/<category_name>/<item_name>/edit', methods=['GET', 'POST'])
@login_required
def editItem(item_name, category_name):

    item = session.query(Item).filter_by(name=item_name).one()
    if item.user_id != login_session['user_id']:
        return '''<script>function myFunction(){alert(
                  'You are not authorized to edit this item.');}
                  </script><body onload='myFunction()''>'''

    if request.method == 'POST':
        if (request.form['name'] != None) and \
           (request.form['description'] != None):
            item.name = request.form['name']
            item.description = request.form['description']
            if item.category.name != request.form['category']:
                newCat = session.query(Category).filter_by(
                         name=request.form['category']).one()
                item.category = newCat

            # save upload file
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = item.name + '.' + file.filename.rsplit('.', 1)[1]
                filename = secure_filename(filename)
                filedir = item.category.name + "/" + filename
                finalDir = os.path.join(app.config['UPLOAD_FOLDER'], filedir)
                file.save(finalDir)
                item.image = filedir

            # save updated item to database
            session.add(item)
            session.commit()
            flash('Item Successfully Edited %s' % item.name)
        return redirect('/catalog')
    # get method
    else:
        category_list = session.query(Category).all()
        return render_template('editItem.html', category_list=category_list,
                               item=item)


@app.route('/catalog/<category_name>/<item_name>/delete', methods=['GET', 'POST'])
@login_required
def deleteItem(item_name, category_name):

    cat = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter_by(name=item_name,
                                         category=cat).one()
    # check for creator
    if item.user_id != login_session['user_id']:
        return '''<script>function myFunction() {alert(
                'You are not authorized to delete this item.');}
                </script><body onload='myFunction()''>'''

    if request.method == 'POST':
        try:
            imgdir = os.path.join(app.config['UPLOAD_FOLDER'], item.image)
            print "delete %s" % imgdir
            if os.path.isfile(imgdir):
                os.unlink(imgdir)
        except Exception, e:
            print e
        session.delete(item)
        flash('%s Successfully Deleted' % item.name)
        session.commit()
        return redirect('/catalog')
    else:
        return render_template('/deleteItem.html', item=item)


# Return all data in JSON format
@app.route('/catalog.json')
def catalogJSON():
    """Return all data in the database in JSON format"""
    cat_list = session.query(Category).all()
    result = []
    for cat in cat_list:
        items = session.query(Item).filter_by(category_id=cat.id).all()
        catObj = dict(id=cat.id, name=cat.name,
                      item=[i.serialize for i in items])
        result.append(catObj)
    return jsonify(Category=result)


# Handle Google API
@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Google connect API"""
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
        oauth_flow = flow_from_clientsecrets('catalog/client_secrets.json',
                                             scope='')
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
        response = make_response(json.dumps(
                                 'Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        print 'Current user is already connected.'
        return response

    # Store the access token in the session for later use.
    # credentials can't be jsonified
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

    # Add provider to login session
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    # Generate output
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px; height: 300px;
               border-radius: 150px;-webkit-border-radius: 150px;
               -moz-border-radius: 150px;"> '''
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """Google disconnect"""
    access_token = login_session['access_token']
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' %\
          login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Facebook API
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    """Facebook connect API"""
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    app_id = json.loads(open('catalog/fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('catalog/fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    # Let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px; height: 300px;border-radius: 150px
                 ;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '''

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    """Facebook disconnect"""
    facebook_id = login_session['facebook_id']

    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % \
        (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


@app.route('/disconnect')
def disconnect():
    """Disconnect based on provider"""
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['provider']
        flash("You have successfully been logged out.")
        print "logged out"
        return redirect('catalog')
    else:
        flash("You were not logged in")
        print "not logged in"
        return redirect('catalog')


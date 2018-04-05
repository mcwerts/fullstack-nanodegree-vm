#!/usr/bin/env python3
"""Simple catalog app"""

import sys
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask import session as login_session
import random, string
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

# IMPORTS FOR Gconect
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.clientsecrets import InvalidClientSecretsError
import httplib2
#import json #repeat
from flask import make_response
import requests

app = Flask(__name__)


CLIENT_ID = json.loads(
  open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "SportsExhange Catalog"

engine = create_engine("sqlite:///catalog.db")
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def lookupJoinTupleByName(category_name, item_name):
  """
  Search inner join of Category and Item tables for category_name and item_name.

  Return (Category, Item) tuple.
  """
  result = session.query(Category, Item).filter(Category.id==Item.category_id).\
    filter(Category.name==category_name).filter(Item.name==item_name).one()
  return result


def print_response_headers(dictionary):
  """Neatly print the response"""
  print("{")
  for k, v in dictionary.items():
    print("  {}: {}".format(k, v))
  print("}")


def clear_login_session():
  """Clear the fields of the login session."""
  print("Clear the login session")
  del login_session['access_token']
  del login_session['gplus_id']
  del login_session['username']
  del login_session['email']
  del login_session['picture']


@app.route('/catalog.json')
def catalogJSON():
  """Show categories and latest items."""
  categories = session.query(Category).all()
  return jsonify(Categories=[i.serialize for i in categories])


@app.route('/login')
def showLogin():
  """Render login page"""
  # This is the anti-forgery state token. Unique value generated for each
  # visit to this route.
  login_session['state'] = ''.join(
    random.choice(string.ascii_uppercase + string.digits) for x in range(32))
  client_id = json.load(open("client_secret.json"))["web"]["client_id"]
  print("Client ID: {}".format(client_id))
  print("Client generated Anti-Forgery State Token: {}".format(
    login_session['state']))
  return render_template(
    'login.html', client_id=client_id, STATE=login_session['state'])

@app.route('/gconnect', methods=['POST'])
def gconnect():
  # Validate anti-forgery state token after round trip to google's auth
  # server. Ensures we are talking to the same "login" that we started with.
  if request.args.get('state') != login_session['state']:
    response = make_response(
      json.dumps('Invalid anti-forgery state token.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response
  print("Anti-Forgery State Token: valid")

  # Obtain authorization code
  print("Obtain authorization code")
  one_time_code = request.data
  print("One time code: {}".format(one_time_code))

  try:
    # Upgrade the authorization code into a credentials object
    oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
    oauth_flow.redirect_uri = 'postmessage'
    # Why are we skipping step 1?
    credentials = oauth_flow.step2_exchange(one_time_code)
  except FlowExchangeError:
    response = make_response(
      json.dumps(
        'FlowExchangeError: Failed to upgrade the authorization code.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Check that the NEW access token is valid. (3 checks)
  access_token = credentials.access_token
  print("Google access token: {}".format(access_token))
  print("Check access token:")

  # Request info on this NEW access token from Google. UPDATED FOR PYTHON 3.
  url = 'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}'.format(
    access_token)
  h = httplib2.Http()
  headers, body_bytes = h.request(url, 'GET')
  print("Response Headers:")
  print_response_headers(headers)
  body_str = body_bytes.decode('utf8')
  body_json = json.loads(body_str)
  print("Response Body(json):")
  print(json.dumps(body_json, sort_keys=False, indent=2))

  # Now check the values in the NEW json body of the response
  # If there was an error in the access token info, abort.
  if body_json.get('error') is not None:
    response = make_response(json.dumps(body_json.get('error')), 500)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Verify that the NEW access token is used for the intended user.
  gplus_id = credentials.id_token['sub']
  if body_json['user_id'] != gplus_id:
    response = make_response(
      json.dumps("Token's user ID doesn't match given user ID."), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Verify that the NEW access token is valid for this app.
  if body_json['issued_to'] != CLIENT_ID:
    response = make_response(
      json.dumps("Token's client ID does not match app's."), 401)
    print("Token's client ID does not match app's.")
    response.headers['Content-Type'] = 'application/json'
    return response

  # DEFECT in sample code
  # If stored access token is expired or revoked, user appears logged in
  # but cannot be disconnected until some unclear mechanism fires (cookies
  # deleted?)

  # Check for stale access token in login_session
  stored_access_token = login_session.get('access_token')
  if stored_access_token is not None and stored_access_token != access_token:
    print("Stale access token: {}".format(stored_access_token))
    clear_login_session()


  # Check if the user is already logged in
  print("Check if the user is already logged in")
  stored_access_token = login_session.get('access_token')
  stored_gplus_id = login_session.get('gplus_id')
  if stored_access_token is not None and gplus_id == stored_gplus_id:
    response = make_response(json.dumps('Current user is already connected.'),
      200)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Store the access token in the session for later use.
  print("Store the access token in the session for later use")
  login_session['access_token'] = credentials.access_token
  login_session['gplus_id'] = gplus_id

  # Get user info
  print("Get user info")
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
  output += ' " style = "width: 300px; height: 300px; border-radius: 150px; -webkit-border-radius: 150px; -moz-border-radius: 150px;"> '
  flash("You are now logged in as {}".format(login_session['username']))
  print("done!")
  return output


@app.route('/gdisconnect')
def gdisconnect():
    """DISCONNECT - Revoke a current user's token and reset their login_session"""
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is {}'.format(access_token))
    print('User name is: ')
    print(login_session['username'])
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    print("url:")
    print(url)
    h = httplib2.Http()
    result, body_bytes = h.request(url, 'GET')
    print('result is ')
    print(result)
    print("status: {}".format(result['status']))
    print('body is: ')
    print(body_bytes.decode('utf8'))
    if result['status'] == '200':
      clear_login_session()
      response = make_response(json.dumps('Successfully disconnected.'), 200)
      response.headers['Content-Type'] = 'application/json'
      return response
    else:
      response = make_response(json.dumps('Failed to revoke token for given user.', 400))
      response.headers['Content-Type'] = 'application/json'
      return response


@app.route('/catalog/<string:category_name>.json')
def showItemsJSON(category_name):
  """Show items in the given category."""
  results = session.query(Category, Item).filter(Category.id==Item.category_id).filter(Category.name==category_name).all()
  return jsonify(Items=[i.serialize for c, i in results])


@app.route('/')
@app.route('/catalog/')
def showCatalog():
  """Show categories and latest items."""
  print("showCatalog")
  categories = session.query(Category).all()
  latest = session.query(Category, Item).filter(Category.id==Item.category_id).order_by(Item.id.desc())
  print("return from showCatalog")
  return render_template('catalog.html', categories=categories, latest=latest)


@app.route('/catalog/<string:category_name>/')
def showItems(category_name):
  """Show items in the given category."""
  results = session.query(Category, Item).filter(Category.id==Item.category_id).filter(Category.name==category_name).all()
  return render_template('items.html',
    category_name=category_name, categories=session.query(Category).all(), items=results)


@app.route('/catalog/<string:category_name>/<string:item_name>/')
def showItemDetails(category_name, item_name):
  join_tuple = lookupJoinTupleByName(category_name, item_name)
  #print(item)
  return render_template('itemDetails.html',
    category_name=category_name, item_name=item_name, item=join_tuple)


@app.route('/catalog/add', methods = ['GET', 'POST'])
def addItem():
  """For GET request, return 'Add Item' page. For POST request, add new item to database."""
  if request.method == 'POST':
    category=request.form['category']
    category_result = session.query(Category).filter_by(name=category).one()
    newItem = Item(name=request.form['name'], description=request.form['description'],
      category_id=category_result.id)
    # need to protect against manually entered bad data

    session.add(newItem)
    session.commit()

    flash("Item added: {} / {}".format(category, newItem.name))

    return redirect(url_for('showCatalog'))
  else:
    categories = session.query(Category).all()
    return render_template('addItem.html', categories=categories)


@app.route('/catalog/<string:category_name>/<string:item_name>/edit', methods = ['GET', 'POST'])
def editItem(category_name, item_name):
  join_tuple = lookupJoinTupleByName(category_name, item_name)
  if request.method == 'POST':
    edited_item = join_tuple[1]

    if request.form['name']:
      name = request.form['name']
      edited_item.name = request.form['name']
    else:
      name = item_name
    if request.form['description']:
      edited_item.description = request.form['description']

    category = request.form['category']
    edited_item.category_id = session.query(Category.id).filter_by(name=request.form['category']).scalar()
    session.add(edited_item)
    session.commit()
    flash("Item edited: {} / {}".format(category, name))
    return redirect(url_for('showCatalog'))
  else:
    item = join_tuple[1]
    print(item)
    return render_template('editItem.html',
      category_name=category_name, item_name=item_name, item=item, categories=session.query(Category).all())


@app.route('/catalog/<string:category_name>/<string:item_name>/delete', methods = ['GET', 'POST'])
def deleteItem(category_name, item_name):
  if request.method == 'POST':
    join_tuple = lookupJoinTupleByName(category_name, item_name)
    item = join_tuple[1]
    session.delete(item)
    session.commit()
    flash("Item deleted: {} / {}".format(category_name, item_name))
    return redirect(url_for('showCatalog'))
  else:
    return render_template('deleteItem.html', category_name=category_name, item_name=item_name)


@app.route('/catalog/<string:category_name>/<string:item_name>/JSON')
def getItemJSON(category_name, item_name):
  return "json data"


if __name__ == '__main__':
  app.secret_key = 'super_secret_key'  #TODO
  app.debug = True
  app.run(host = '0.0.0.0', port = 8000)


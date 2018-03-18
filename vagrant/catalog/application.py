#!/usr/bin/env python3
"""Simple catalog app"""

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

categories = [
  {'name': 'Baseball', "category_id": 3},
  {'name': 'Hockey', "category_id": 1},
  {'name': 'Soccer', "category_id": 2}
  ]

item = {'name': 'Bat', 'description': 'Top quality ash bat for banging out homers!'}

items = [
  {'name': 'Bat', "category_id": 3},
  {'name': 'Stick', "category_id": 1},
  {'name': 'Ball', "category_id": 2},
  {'name': 'Ball', "category_id": 3},
  {'name': 'Goal', "category_id": 2},
  {'name': 'Glove', "category_id": 3},
  {'name': 'Skates', "category_id": 1},
  {'name': 'Helmet', "category_id": 1},
  ]

latest = [
  {'name': 'Bat', "category_id": 3},
  {'name': 'Stick', "category_id": 1},
  {'name': 'Ball', "category_id": 2},
  {'name': 'Ball', "category_id": 3},
  ]

@app.route('/')
@app.route('/catalog/')
def showCatalog():
  return render_template('catalog.html', categories=categories, latest=latest)

@app.route('/catalog/<string:category_name>/')
def showItems(category_name):
  return render_template('items.html', category_name=category_name, categories=categories, items=items)

@app.route('/catalog/<string:category_name>/<string:item_name>/')
def showItemDetails(category_name, item_name):
  return render_template('itemDetails.html', category_name=category_name, item_name=item_name, item=item)


@app.route('/catalog/add', methods = ['GET', 'POST'])
def addItem():
  if request.method == 'POST':
    return redirect(url_for('showCatalog'))
  else:
    return render_template('addItem.html')


@app.route('/catalog/<string:category_name>/<string:item_name>/edit', methods = ['GET', 'POST'])
def editItem(category_name, item_name):
  if request.method == 'POST':
    return redirect(url_for('showCatalog'))
  else:
    return render_template('editItem.html', category_name=category_name, item_name=item_name)


@app.route('/catalog/<string:category_name>/<string:item_name>/delete', methods = ['GET', 'POST'])
def deleteItem(category_name, item_name):
  if request.method == 'POST':
    return redirect(url_for('showCatalog'))
  else:
    return render_template('deleteItem.html', category_name=category_name, item_name=item_name)


@app.route('/catalog/<string:category_name>/<string:item_name>/JSON')
def getItemJSON(category_name, item_name):
  return "json data"


if __name__ == '__main__':
  app.debug = True
  app.run(host = '0.0.0.0', port = 8000)


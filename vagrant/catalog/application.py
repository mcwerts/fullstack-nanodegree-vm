#!/usr/bin/env python3
"""Simple catalog app"""

from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

app = Flask(__name__)

engine = create_engine("sqlite:///catalog.db")
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


fake_categories = [
  {'name': 'Baseball', "category_id": 3},
  {'name': 'Hockey', "category_id": 1},
  {'name': 'Soccer', "category_id": 2}
  ]

fake_item = {'name': 'Bat', 'description': 'Top quality ash bat for banging out homers!'}

fake_items = [
  {'name': 'Bat', "category_id": 3},
  {'name': 'Stick', "category_id": 1},
  {'name': 'Ball', "category_id": 2},
  {'name': 'Ball', "category_id": 3},
  {'name': 'Goal', "category_id": 2},
  {'name': 'Glove', "category_id": 3},
  {'name': 'Skates', "category_id": 1},
  {'name': 'Helmet', "category_id": 1},
  ]

fake_latest = [
  {'name': 'Bat', "category": "Baseball"},
  {'name': 'Stick', "category": "Hockey"},
  {'name': 'Ball', "category": "Soccer"},
  {'name': 'Ball', "category": "Baseball"},
  ]


def lookupJoinTupleByName(category_name, item_name):
  result = session.query(Category, Item).filter(Category.id==Item.category_id).\
    filter(Category.name==category_name).filter(Item.name==item_name).one()
  return result

@app.route('/')
@app.route('/catalog/')
def showCatalog():
  """Show categories and latest items."""
  categories = session.query(Category).all()
  latest = session.query(Category, Item).filter(Category.id==Item.category_id).order_by(Item.id.desc())
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
  print(item)
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

    return redirect(url_for('showCatalog'))
  else:
    categories = session.query(Category).all()
    return render_template('addItem.html', categories=categories)





@app.route('/catalog/<string:category_name>/<string:item_name>/edit', methods = ['GET', 'POST'])
def editItem(category_name, item_name):
  item_tuple = lookupJoinTupleByName(category_name, item_name)
  if request.method == 'POST':
    edited_item = item_tuple[1]
    if request.form['name']:
      edited_item.name = request.form['name']
    if request.form['description']:
      edited_item.description = request.form['description']
    session.add(edited_item)
    session.commit()
    #should we redirect to edited item?
    return redirect(url_for('showCatalog'))
  else:
    item = item_tuple[1]
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
    return redirect(url_for('showCatalog'))
  else:
    return render_template('deleteItem.html', category_name=category_name, item_name=item_name)


@app.route('/catalog/<string:category_name>/<string:item_name>/JSON')
def getItemJSON(category_name, item_name):
  return "json data"


if __name__ == '__main__':
  app.debug = True
  app.run(host = '0.0.0.0', port = 8000)


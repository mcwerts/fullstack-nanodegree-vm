#!/usr/bin/env python3
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class Category(Base):
  __tablename__ = 'category'
  name = Column(String(80), nullable = False)
  id = Column(Integer, primary_key = True)

  def __repr__(self):
    return "<Category(name={}, id={})>".format(self.name, self.id)

  @property
  def serialize(self):
    """Returns Category data in an easily serializable format"""
    return {
      'name' : self.name,
      'id' : self.id,
    }


class Item(Base):
  __tablename__ = 'item'
  name = Column(String(80), nullable = False)
  id = Column(Integer, primary_key = True)
  description = Column(String(250))
  category_id = Column(Integer, ForeignKey('category.id'))
  category = relationship(Category)

  def __repr__(self):
    return "<Item(name={}, id={}, description={}, category_id={})>".format(self.name,
      self.id, self.description, self.category_id)

  @property
  def serialize(self):
    """Returns Item data in an easily serializable format"""
    return {
      'name' : self.name,
      'id' : self.id,
      'description' : self.description,
      'category_id' : self.category_id,
    }

engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Item

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


category = Category(name="Baseball")
session.add(category)
session.commit()

category = Category(name="Basketball")
session.add(category)
session.commit()

category = Category(name="Soccer")
session.add(category)
session.commit()

category = Category(name="Frisbee")
session.add(category)
session.commit()

category = Category(name="Snowboarding")
session.add(category)
session.commit()

category = Category(name="Rock Climbing")
session.add(category)
session.commit()

category = Category(name="Foosball")
session.add(category)
session.commit()

category = Category(name="Skating")
session.add(category)
session.commit()

category = Category(name="Hockey")
session.add(category)
session.commit()

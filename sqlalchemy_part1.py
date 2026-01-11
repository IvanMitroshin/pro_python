from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

class Database:
    def __init__(self, db_url="sqlite:///woysa.db"):
        self.engine = create_engine(db_url)
        self.Base = declarative_base()
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        self.Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.Session()

db = Database()

class BaseTable(db.Base):
    __abstract__ = True

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

class Supplier(BaseTable):
    __tablename__ = 'suppliers'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

class Product(BaseTable):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)

class Order(BaseTable):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    order_date = Column(String(50))
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)

db.create_tables()

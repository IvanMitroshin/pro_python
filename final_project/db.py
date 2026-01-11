from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.orm import declarative_base, sessionmaker

class Database:
    def __init__(self, db_url="sqlite:///woysa_sales.db"):
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

class Seller(BaseTable):
    __tablename__ = 'sellers'
    id = Column(Integer, primary_key=True)
    seller_id = Column(String(100), nullable=False)
    name = Column(String(200))
    store = Column(String(200))
    brand = Column(String(200))

class SKU(BaseTable):
    __tablename__ = 'skus'
    id = Column(Integer, primary_key=True)
    sku_id = Column(String(100), nullable=False)
    name = Column(String(500))
    category_id = Column(Integer, nullable=False)
    seller_id = Column(String(100), nullable=False)
    price = Column(Float)
    sum_sale = Column(Float)
    additional_data = Column(Text)

db.create_tables()
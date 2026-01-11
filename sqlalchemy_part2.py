import asyncio
import aiohttp
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

class BaseParser:
    def loader(self, categories):
        pass

    def to_dict(self, data):
        pass


class WoysaParser(BaseParser):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.base_url = "https://analitika.woysa.club/images/panel/json/download/niches.php"

    async def download(self, session, skip, category):
        url = self.base_url + f"?skip={skip}&price_min=0&price_max=1060225&up_vy_min=0&up_vy_max=108682515&up_vy_pr_min=0&up_vy_pr_max=2900&sum_min=1000&sum_max=82432725&feedbacks_min=0&feedbacks_max=32767&trend=false&sort=sum_sale&sort_dir=-1&id_cat={category}"
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return []

    async def loader(self, categories):
        all_data = []
        async with aiohttp.ClientSession() as session:
            tasks = []
            for cat in categories:
                for skip in [0, 100, 200]:
                    task = self.download(session, skip, cat)
                    tasks.append(task)

            for task in asyncio.as_completed(tasks):
                page_data = await task
                if page_data:
                    all_data.extend(page_data)

        return all_data

    def to_dict(self, data):
        result = {
            "total": len(data),
            "by_category": {}
        }
        for item in data:
            if isinstance(item, dict):
                cat = item.get("id_cat", "unknown")
                if cat not in result["by_category"]:
                    result["by_category"][cat] = []
                result["by_category"][cat].append(item)
        return result


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
    products = relationship("Product", back_populates="supplier")


class Product(BaseTable):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    supplier = relationship("Supplier", back_populates="products")
    orders = relationship("Order", back_populates="product")


class Order(BaseTable):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    order_date = Column(String(50))
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product = relationship("Product", back_populates="orders")

db.create_tables()

class OrderFiller:
    def __init__(self):
        self.parser = WoysaParser()

    async def fill_orders(self):

        woysa_items = await self.parser.loader([1, 2, 3])
        if not woysa_items:
            return False
        session = db.get_session()
        suppliers = [Supplier(name=f"Поставщик {i}") for i in range(1, 4)]
        session.add_all(suppliers)
        session.commit()

        products = []
        for idx, item in enumerate(woysa_items[:10]):
                name = item.get("name", f"Товар {idx}")
                price_str = item.get("price", "10.0")
                price = float(price_str)
                supplier = suppliers[idx % len(suppliers)]
                product = Product(
                    name=name[:100],
                    price=price,
                    supplier=supplier
                )
                products.append(product)


        session.add_all(products)
        session.commit()

        orders = []
        for product in products:
            order = Order(
                order_date=datetime.now().strftime("%Y-%m-%d"),
                quantity=1,
                total_price=product.price,
                product=product
            )
            orders.append(order)
        session.add_all(orders)
        session.commit()
        return True

def display_orders():
    session = db.get_session()
    orders = session.query(Order).order_by(Order.order_date.desc()).limit(10).all()

    for i, order in enumerate(orders, 1):
        print(f"\n{i}. Заказ #{order.id}")
        print(f"   Дата: {order.order_date}")
        print(f"   Товар: {order.product.name}")
        print(f"   Поставщик: {order.product.supplier.name}")
        print(f"   Количество: {order.quantity}")
        print(f"   Сумма: ${order.total_price:.2f}")

    session.close()


async def main():

    display_orders()


import asyncio
import aiohttp
import json
import uvicorn
from api import app
from db import db, Seller, SKU


class WoysaParser:
    def __init__(self):
        self.base_url = "https://analitika.woysa.club/images/panel/json/download/niches.php"

    async def download(self, session, skip, category):
        url = self.base_url + f"?skip={skip}&id_cat={category}"
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return []

    async def load_category(self, category):
        all_data = []
        async with aiohttp.ClientSession() as session:
            tasks = []
            for skip in [0, 100, 200]:
                task = self.download(session, skip, category)
                tasks.append(task)

            for task in asyncio.as_completed(tasks):
                page_data = await task
                if page_data:
                    all_data.extend(page_data)

        return all_data


class DataService:
    def __init__(self):
        self.parser = WoysaParser()

    async def load_and_save_data(self):

        for category_id in [1, 2, 3]:
            print(f"Загрузка категории {category_id}...")
            raw_data = await self.parser.load_category(category_id)

            if not raw_data:
                print(f"Нет данных {category_id}")
                continue

            session = db.get_session()
            sellers_seen = set()
            skus_seen = set()

            for item in raw_data:
                if not isinstance(item, dict):
                    continue

                seller_id = str(item.get('id', '')) or str(item.get('seller_id', ''))
                if not seller_id:
                    continue

                if seller_id not in sellers_seen:
                    seller = Seller(
                        seller_id=seller_id,
                        name=item.get('name', '')[:200],
                        store=item.get('store', ''),
                        brand=item.get('brand', '')
                    )
                    session.add(seller)
                    sellers_seen.add(seller_id)

                sku_id = str(item.get('id_cat', '')) + "_" + seller_id
                if sku_id not in skus_seen:
                    additional = {
                        'up_vy': item.get('up_vy'),
                        'up_vy_pr': item.get('up_vy_pr'),
                        'feedbacks': item.get('feedbacks'),
                        'trend': item.get('trend')
                    }

                    sku = SKU(
                        sku_id=sku_id,
                        name=item.get('name', '')[:500],
                        category_id=category_id,
                        seller_id=seller_id,
                        price=float(item.get('price', 0)),
                        sum_sale=float(item.get('sum_sale', 0)),
                        additional_data=json.dumps(additional)
                    )
                    session.add(sku)
                    skus_seen.add(sku_id)

            session.commit()
            session.close()

            print(f"Категория {category_id}: {len(sellers_seen)} продавцов, {len(skus_seen)} SKU")


data_service = DataService()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(data_service.load_and_save_data())


def run_api():
    print("Запуск API")
    print("API: http://localhost:8000/docs")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )

if __name__ == "__main__":
    run_api()
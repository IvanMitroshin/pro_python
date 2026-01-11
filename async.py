import asyncio
import aiohttp
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





import requests

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

    def download(self, skip, category):
        url = self.base_url + f"?skip={skip}&price_min=0&price_max=1060225&up_vy_min=0&up_vy_max=108682515&up_vy_pr_min=0&up_vy_pr_max=2900&sum_min=1000&sum_max=82432725&feedbacks_min=0&feedbacks_max=32767&trend=false&sort=sum_sale&sort_dir=-1&id_cat={category}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()

    def loader(self, categories):
        all_data = []

        for category in categories:
            for page in range(10):
                skip = page * 100
                data = self.download(skip, category)
                if data:
                    all_data.extend(data)

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


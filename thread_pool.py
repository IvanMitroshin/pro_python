from concurrent.futures import ThreadPoolExecutor
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

    def download(self, category):
        url = f"{self.base_url}?id_cat={category}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()

    def loader(self, categories):
        all_data = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            results = executor.map(self.download, categories)
            for result in results:
                all_data.extend(result)
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


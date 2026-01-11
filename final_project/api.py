import json
import redis
from typing import Optional, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import db, Seller, SKU
from sqlalchemy import func

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 1
CACHE_TTL = 300

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)


class CacheManager:
    @staticmethod
    def generate_cache_key(endpoint: str, **kwargs) -> str:
        key_parts = [f"api:{endpoint}"]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)

    @staticmethod
    def get_from_cache(key: str) -> Optional[Any]:
        try:
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
        except:
            pass
        return None

    @staticmethod
    def set_to_cache(key: str, data: Any, ttl: int = CACHE_TTL):
        try:
            redis_client.setex(key, ttl, json.dumps(data, default=str))
        except:
            pass


class SellerResponse(BaseModel):
    id: int
    seller_id: str
    name: Optional[str]
    store: Optional[str]
    brand: Optional[str]

    class Config:
        from_attributes = True


class SKUResponse(BaseModel):
    id: int
    sku_id: str
    name: str
    category_id: int
    seller_id: str
    price: Optional[float]
    sum_sale: Optional[float]

    class Config:
        from_attributes = True


app = FastAPI(
    title="API",
    description="API по продовцам WB",
    version="1.0.0"
)


@app.get("/category/{category_id}")
async def get_category_data(category_id: int):
    cache_key = CacheManager.generate_cache_key("category", id=category_id)
    cached = CacheManager.get_from_cache(cache_key)
    if cached is not None:
        return cached

    session = db.get_session()
    skus = session.query(SKU).filter(SKU.category_id == category_id).all()

    if not skus:
        session.close()
        raise HTTPException(status_code=404, detail=f"Нет данных для категории {category_id}")

    seller_ids = list(set([sku.seller_id for sku in skus]))
    sellers = session.query(Seller).filter(Seller.seller_id.in_(seller_ids)).all()

    response = {
        "category_id": category_id,
        "total_skus": len(skus),
        "total_sellers": len(sellers),
        "sellers": [SellerResponse.from_orm(seller).dict() for seller in sellers],
        "skus": [SKUResponse.from_orm(sku).dict() for sku in skus[:100]]
    }

    session.close()
    CacheManager.set_to_cache(cache_key, response)
    return response


@app.get("/sallesr/")
async def get_all_sellers(limit: int = 100, offset: int = 0):
    cache_key = CacheManager.generate_cache_key("all_sellers", limit=limit, offset=offset)
    cached = CacheManager.get_from_cache(cache_key)
    if cached is not None:
        return cached

    session = db.get_session()
    sellers = session.query(Seller).offset(offset).limit(limit).all()
    total = session.query(func.count(Seller.id)).scalar()
    session.close()

    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "sellers": [SellerResponse.from_orm(seller).dict() for seller in sellers]
    }

    CacheManager.set_to_cache(cache_key, response)
    return response


@app.get("/sallesr/{seller_id}")
async def get_seller_sales(seller_id: str):
    cache_key = CacheManager.generate_cache_key("seller_sales", id=seller_id)
    cached = CacheManager.get_from_cache(cache_key)
    if cached is not None:
        return cached

    session = db.get_session()
    seller = session.query(Seller).filter(Seller.seller_id == seller_id).first()

    if not seller:
        session.close()
        raise HTTPException(status_code=404, detail=f"Продавец {seller_id} не найден")

    skus = session.query(SKU).filter(SKU.seller_id == seller_id).all()
    session.close()
    total_sales = sum(sku.sum_sale or 0 for sku in skus)
    total_skus = len(skus)

    response = {
        "seller": SellerResponse.from_orm(seller).dict(),
        "statistics": {
            "total_skus": total_skus,
            "total_sales": total_sales,
            "average_price": total_sales / total_skus if total_skus > 0 else 0
        },
        "skus": [SKUResponse.from_orm(sku).dict() for sku in skus[:50]]
    }

    CacheManager.set_to_cache(cache_key, response)
    return response


@app.get("/products/")
async def get_all_products(limit: int = 100, offset: int = 0):
    cache_key = CacheManager.generate_cache_key("all_products", limit=limit, offset=offset)
    cached = CacheManager.get_from_cache(cache_key)
    if cached is not None:
        return cached

    session = db.get_session()
    skus = session.query(SKU).offset(offset).limit(limit).all()
    total = session.query(func.count(SKU.id)).scalar()
    session.close()

    response = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "products": [SKUResponse.from_orm(sku).dict() for sku in skus]
    }

    CacheManager.set_to_cache(cache_key, response)
    return response
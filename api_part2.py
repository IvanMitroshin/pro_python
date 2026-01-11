import json
from datetime import datetime
from typing import Optional, Any
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import uvicorn

class SupplierBase(BaseModel):
    name: str

class SupplierUpdate(BaseModel):
    name: Optional[str] = None

class SupplierResponse(SupplierBase):
    id: int

    class Config:
        from_attributes = True


REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
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

    @staticmethod
    def invalidate_cache(pattern: str = "api:*"):
        try:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
        except:
            pass


app = FastAPI(
    title="Woysa API Redis",
    description="API для работы с поставщиками",
    version="1.0.0"
)


class StatisticsRequest(BaseModel):
    email: EmailStr


@app.get("/sallers")
async def get_all_suppliers():
    cache_key = CacheManager.generate_cache_key("all_suppliers")
    cached = CacheManager.get_from_cache(cache_key)
    if cached is not None:
        return cached
    session = db.get_session()
    suppliers = session.query(Supplier).all()
    result = [{"id": s.id, "name": s.name} for s in suppliers]
    session.close()
    CacheManager.set_to_cache(cache_key, result)
    return result


@app.get("/sallers/{supplier_id}")
async def get_supplier_by_id(supplier_id: int):
    cache_key = CacheManager.generate_cache_key("supplier_by_id", id=supplier_id)
    cached = CacheManager.get_from_cache(cache_key)
    if cached is not None:
        return cached
    session = db.get_session()
    supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
    session.close()
    if not supplier:
        raise HTTPException(status_code=404, detail="Поставщик не найден")
    result = {"id": supplier.id, "name": supplier.name}
    CacheManager.set_to_cache(cache_key, result)
    return result


@app.put("/sallers/{supplier_id}/update")
async def update_supplier(supplier_id: int, name: str):
    session = db.get_session()
    supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        session.close()
        raise HTTPException(status_code=404, detail="Поставщик не найден")
    supplier.name = name
    session.commit()
    session.close()
    CacheManager.invalidate_cache("api:*supplier*")
    return {"updated": True, "id": supplier_id, "name": name}


@app.post("/statistics/")
async def get_statistics(request: StatisticsRequest):
    cache_key = CacheManager.generate_cache_key("statistics", email=request.email)
    cached = CacheManager.get_from_cache(cache_key)
    if cached:
        return {"cached": True, "data": cached}
    session = db.get_session()
    suppliers_count = session.query(Supplier).count()
    session.close()
    stats = {
        "suppliers_count": suppliers_count,
        "email": request.email,
        "timestamp": datetime.now().isoformat(),
    }
    CacheManager.set_to_cache(cache_key, stats)
    return {"data": stats}


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
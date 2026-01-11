from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import uvicorn


class SupplierBase(BaseModel):
    name: str

class SupplierUpdate(BaseModel):
    name: Optional[str] = None

class SupplierResponse(SupplierBase):
    id: int

    class Config:
        from_attributes = True


app = FastAPI(
    title="Woysa API",
    description="API для работы с поставщиками",
    version="1.0.0"
)


@app.get("/sallers", response_model=List[SupplierResponse])
async def get_all_suppliers():
    session = db.get_session()
    suppliers = session.query(Supplier).order_by(Supplier.id).all()
    session.close()
    return suppliers


@app.get("/sallers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier_by_id(supplier_id: int):
    session = db.get_session()
    supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
    session.close()
    return supplier


@app.put("/sallers/{supplier_id}/update", response_model=SupplierResponse)
async def update_supplier(supplier_id: int, supplier_update: SupplierUpdate):
    session = db.get_session()
    supplier = session.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier_update.name is not None:
        supplier.name = supplier_update.name
    session.commit()
    session.refresh(supplier)
    session.close()
    return supplier


def run_api():
    print(" Запуск API")
    print("API: http://localhost:8000/docs")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )


if __name__ == "__main__":
    run_api()
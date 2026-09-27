from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import PurchaseOrder, Vendor

router = APIRouter(prefix="/pos", tags=["purchase_orders"])

class POCreate(BaseModel):
    po_number: str
    vendor_id: int
    product_name: str
    quantity: float = 1.0
    unit_price: float
    total_amount: float
    line_items: Optional[list] = None

@router.get("")
def list_purchase_orders(db: Session = Depends(get_db)):
    pos = db.query(PurchaseOrder).order_by(PurchaseOrder.created_at.desc()).all()
    result = []
    for po in pos:
        result.append({
            "id": po.id,
            "po_number": po.po_number,
            "vendor_id": po.vendor_id,
            "vendor_name": po.vendor.name if po.vendor else "Unknown",
            "product_name": po.product_name,
            "quantity": po.quantity,
            "unit_price": po.unit_price,
            "total_amount": po.total_amount,
            "line_items": po.line_items,
            "created_at": str(po.created_at)
        })
    return result

@router.post("")
def create_purchase_order(data: POCreate, db: Session = Depends(get_db)):
    existing = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == data.po_number).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"PO #{data.po_number} already exists")

    po = PurchaseOrder(
        po_number=data.po_number,
        vendor_id=data.vendor_id,
        product_name=data.product_name,
        quantity=data.quantity,
        unit_price=data.unit_price,
        total_amount=data.total_amount,
        line_items=data.line_items or [{"description": data.product_name, "qty": data.quantity, "price": data.unit_price}]
    )
    db.add(po)
    db.commit()
    db.refresh(po)
    return po

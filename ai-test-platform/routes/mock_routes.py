"""
Phase 17: Demo Mock API 路由
提供 17 个模拟业务接口，支持正常和异常场景。
"""
import copy
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Header, HTTPException, Path, Body

router = APIRouter(prefix="/api/mock", tags=["MockAPI"])

# ── 内存数据 (可重复初始化) ──────────────────────────
_VALID_TOKEN = "demo-token"

_products: Dict[str, dict] = {}
_orders: Dict[str, dict] = {}
_bills: Dict[str, dict] = {}
_id_counter = {"product": 100, "order": 200, "bill": 300}


def reset_mock_data():
    """重置所有 Mock 内存数据"""
    global _products, _orders, _bills, _id_counter
    _products = {
        "1": {"id": "1", "name": "ERP基础模块", "price": 9999.0, "stock": 50, "category": "软件", "created_at": "2026-01-01"},
        "2": {"id": "2", "name": "财务管理系统", "price": 19999.0, "stock": 20, "category": "软件", "created_at": "2026-01-02"},
        "3": {"id": "3", "name": "供应链平台", "price": 29999.0, "stock": 10, "category": "平台", "created_at": "2026-01-03"},
    }
    _orders = {
        "1": {"id": "1", "product_id": "1", "quantity": 2, "total": 19998.0, "status": "pending", "created_at": "2026-03-01"},
        "2": {"id": "2", "product_id": "2", "quantity": 1, "total": 19999.0, "status": "completed", "created_at": "2026-03-02"},
        "3": {"id": "3", "product_id": "3", "quantity": 1, "total": 29999.0, "status": "cancelled", "created_at": "2026-03-03"},
    }
    _bills = {
        "1": {"id": "1", "order_id": "1", "amount": 19998.0, "status": "draft", "created_at": "2026-04-01"},
        "2": {"id": "2", "order_id": "2", "amount": 19999.0, "status": "submitted", "created_at": "2026-04-02"},
        "3": {"id": "3", "order_id": "2", "amount": 19999.0, "status": "approved", "created_at": "2026-04-03"},
        "4": {"id": "4", "order_id": "1", "amount": 5000.0, "status": "paid", "created_at": "2026-04-04"},
    }
    _id_counter.update({"product": 100, "order": 200, "bill": 300})


# 首次加载时初始化
reset_mock_data()


def _ok(data: Any = None, message: str = "success") -> dict:
    return {"code": 0, "message": message, "data": data}


def _biz_error(code: int, message: str) -> dict:
    return {"code": code, "message": message, "data": None}


def _check_auth(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized: missing or invalid token")
    token = authorization.split(" ", 1)[1]
    if token != _VALID_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid token")


# ==================== Auth ====================

@router.post("/login")
async def mock_login(body: dict = Body(...)):
    username = body.get("username", "")
    password = body.get("password", "")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password are required")
    if username == "admin" and password == "123456":
        return _ok({"token": _VALID_TOKEN, "username": "admin", "role": "admin"})
    raise HTTPException(status_code=401, detail="Invalid username or password")


# ==================== User ====================

@router.get("/users/profile")
async def mock_user_profile(authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    return _ok({
        "user_id": "U001",
        "username": "admin",
        "name": "Demo管理员",
        "email": "admin@erp-demo.com",
        "role": "admin",
        "department": "信息部",
    })


# ==================== Product ====================

@router.get("/products")
async def mock_product_list(
    authorization: Optional[str] = Header(None),
    keyword: str = "",
    page: int = 1,
    page_size: int = 20,
):
    _check_auth(authorization)
    items = list(_products.values())
    if keyword:
        items = [p for p in items if keyword.lower() in p["name"].lower()]
    total = len(items)
    start = (page - 1) * page_size
    return _ok({
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items[start:start + page_size],
    })


@router.get("/products/{product_id}")
async def mock_product_detail(
    product_id: str = Path(...),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    p = _products.get(product_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return _ok(p)


@router.post("/products")
async def mock_create_product(
    body: dict = Body(...),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    if not body.get("name"):
        raise HTTPException(status_code=400, detail="name is required")
    if not body.get("price"):
        raise HTTPException(status_code=400, detail="price is required")
    _id_counter["product"] += 1
    pid = str(_id_counter["product"])
    product = {
        "id": pid,
        "name": body["name"],
        "price": float(body["price"]),
        "stock": body.get("stock", 0),
        "category": body.get("category", ""),
        "created_at": datetime.now().strftime("%Y-%m-%d"),
    }
    _products[pid] = product
    return _ok(product, "Product created")


@router.put("/products/{product_id}")
async def mock_update_product(
    product_id: str = Path(...),
    body: dict = Body(...),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    p = _products.get(product_id)
    if not p:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    for k in ("name", "price", "stock", "category"):
        if k in body:
            p[k] = body[k]
    return _ok(p, "Product updated")


@router.delete("/products/{product_id}")
async def mock_delete_product(
    product_id: str = Path(...),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    p = _products.pop(product_id, None)
    if not p:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return _ok({"id": product_id}, "Product deleted")


# ==================== Order ====================

@router.get("/orders")
async def mock_order_list(
    authorization: Optional[str] = Header(None),
    status: str = "",
    page: int = 1,
    page_size: int = 20,
):
    _check_auth(authorization)
    items = list(_orders.values())
    if status:
        items = [o for o in items if o["status"] == status]
    total = len(items)
    start = (page - 1) * page_size
    return _ok({"total": total, "page": page, "page_size": page_size, "items": items[start:start + page_size]})


@router.get("/orders/{order_id}")
async def mock_order_detail(
    order_id: str = Path(...),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    o = _orders.get(order_id)
    if not o:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return _ok(o)


@router.post("/orders")
async def mock_create_order(
    body: dict = Body(...),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    if not body.get("product_id"):
        raise HTTPException(status_code=400, detail="product_id is required")
    if not body.get("quantity"):
        raise HTTPException(status_code=400, detail="quantity is required")
    pid = str(body["product_id"])
    product = _products.get(pid)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {pid} not found")
    _id_counter["order"] += 1
    oid = str(_id_counter["order"])
    order = {
        "id": oid,
        "product_id": pid,
        "quantity": int(body["quantity"]),
        "total": product["price"] * int(body["quantity"]),
        "status": "pending",
        "created_at": datetime.now().strftime("%Y-%m-%d"),
    }
    _orders[oid] = order
    return _ok(order, "Order created")


@router.post("/orders/{order_id}/cancel")
async def mock_cancel_order(
    order_id: str = Path(...),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    o = _orders.get(order_id)
    if not o:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    if o["status"] == "cancelled":
        return _biz_error(40001, "Order already cancelled")
    if o["status"] == "completed":
        return _biz_error(40002, "Cannot cancel a completed order")
    o["status"] = "cancelled"
    return _ok(o, "Order cancelled")


# ==================== Payment Bill ====================

@router.get("/payment-bills")
async def mock_bill_list(
    authorization: Optional[str] = Header(None),
    status: str = "",
    page: int = 1,
    page_size: int = 20,
):
    _check_auth(authorization)
    items = list(_bills.values())
    if status:
        items = [b for b in items if b["status"] == status]
    total = len(items)
    start = (page - 1) * page_size
    return _ok({"total": total, "page": page, "page_size": page_size, "items": items[start:start + page_size]})


@router.get("/payment-bills/{bill_id}")
async def mock_bill_detail(
    bill_id: str = Path(...),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    b = _bills.get(bill_id)
    if not b:
        raise HTTPException(status_code=404, detail=f"PaymentBill {bill_id} not found")
    return _ok(b)


@router.post("/payment-bills/{bill_id}/submit")
async def mock_bill_submit(
    bill_id: str = Path(...),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    b = _bills.get(bill_id)
    if not b:
        raise HTTPException(status_code=404, detail=f"PaymentBill {bill_id} not found")
    if b["status"] != "draft":
        return _biz_error(40003, f"Cannot submit bill in status '{b['status']}', must be 'draft'")
    b["status"] = "submitted"
    return _ok(b, "Bill submitted")


@router.post("/payment-bills/{bill_id}/approve")
async def mock_bill_approve(
    bill_id: str = Path(...),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    b = _bills.get(bill_id)
    if not b:
        raise HTTPException(status_code=404, detail=f"PaymentBill {bill_id} not found")
    if b["status"] != "submitted":
        return _biz_error(40004, f"Cannot approve bill in status '{b['status']}', must be 'submitted'")
    b["status"] = "approved"
    return _ok(b, "Bill approved")


@router.post("/payment-bills/{bill_id}/pay")
async def mock_bill_pay(
    bill_id: str = Path(...),
    authorization: Optional[str] = Header(None),
):
    _check_auth(authorization)
    b = _bills.get(bill_id)
    if not b:
        raise HTTPException(status_code=404, detail=f"PaymentBill {bill_id} not found")
    if b["status"] == "paid":
        return _biz_error(40005, "Bill already paid, cannot pay again")
    if b["status"] != "approved":
        return _biz_error(40006, f"Cannot pay bill in status '{b['status']}', must be 'approved'")
    b["status"] = "paid"
    return _ok(b, "Bill paid")


# ==================== Report ====================

@router.get("/reports/summary")
async def mock_report_summary(authorization: Optional[str] = Header(None)):
    _check_auth(authorization)
    return _ok({
        "total_products": len(_products),
        "total_orders": len(_orders),
        "total_bills": len(_bills),
        "total_revenue": sum(o["total"] for o in _orders.values() if o["status"] != "cancelled"),
        "paid_amount": sum(b["amount"] for b in _bills.values() if b["status"] == "paid"),
        "pending_orders": sum(1 for o in _orders.values() if o["status"] == "pending"),
        "report_date": datetime.now().strftime("%Y-%m-%d"),
    })

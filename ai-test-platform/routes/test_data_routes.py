#!/usr/bin/env python3
"""
P3-2 测试数据管理路由
10 个端点: 数据集 CRUD + 数据项 CRUD + 绑定 + 查询绑定 + 变量替换预览
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from database.models import TestDataset, TestDatasetItem, TestDataBinding, TestCase
from services.test_data_service import (
    mask_sensitive, is_sensitive_key, resolve_variables, substitute,
    validate_dataset, execute_cleanup,
)
from backend.danger_guard import check_confirm, ConfirmRequest

router = APIRouter(prefix="/api/v2/test-data", tags=["测试数据管理"])


# ── Schemas ──────────────────────────────────────────────

class DatasetCreate(BaseModel):
    name: str
    description: str = ""
    project_id: Optional[int] = None
    dataset_type: str = "common_fixture"
    case_type: str = "api"
    tags: list = []

class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dataset_type: Optional[str] = None
    case_type: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[list] = None

class ItemCreate(BaseModel):
    key: str
    value_json: Any = None
    is_sensitive: bool = False
    enabled: bool = True
    sort_order: int = 0

class ItemUpdate(BaseModel):
    key: Optional[str] = None
    value_json: Any = None
    is_sensitive: Optional[bool] = None
    enabled: Optional[bool] = None
    sort_order: Optional[int] = None

class BindingCreate(BaseModel):
    dataset_id: int
    case_id: str
    binding_type: str = "input"

class SubstitutePreview(BaseModel):
    case_id: str
    template: Any = None

class CleanupRequest(BaseModel):
    dataset_id: int
    case_id: str = ""
    allow_cleanup: bool = False


# ── Helpers ──────────────────────────────────────────────

def _serialize_dataset(ds: TestDataset, db: Session) -> dict:
    item_count = db.query(func.count(TestDatasetItem.id)).filter(TestDatasetItem.dataset_id == ds.id).scalar() or 0
    binding_count = db.query(func.count(TestDataBinding.id)).filter(TestDataBinding.dataset_id == ds.id).scalar() or 0
    return {
        "id": ds.id,
        "name": ds.name,
        "description": ds.description,
        "project_id": ds.project_id,
        "dataset_type": ds.dataset_type,
        "case_type": ds.case_type,
        "status": ds.status,
        "tags": ds.tags or [],
        "item_count": item_count,
        "binding_count": binding_count,
        "created_at": ds.created_at.isoformat() if ds.created_at else None,
        "updated_at": ds.updated_at.isoformat() if ds.updated_at else None,
    }

def _serialize_item(item: TestDatasetItem) -> dict:
    val = item.value_json
    if item.is_sensitive or is_sensitive_key(item.key):
        val = mask_sensitive(item.key, val)
    return {
        "id": item.id,
        "dataset_id": item.dataset_id,
        "key": item.key,
        "value_json": val,
        "is_sensitive": item.is_sensitive or is_sensitive_key(item.key),
        "enabled": item.enabled,
        "sort_order": item.sort_order,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


# ── 1. Create dataset ───────────────────────────────────

@router.post("/datasets")
def create_dataset(req: DatasetCreate, db: Session = Depends(get_db)):
    ds = TestDataset(
        name=req.name,
        description=req.description,
        project_id=req.project_id,
        dataset_type=req.dataset_type,
        case_type=req.case_type,
        tags=req.tags or [],
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return _serialize_dataset(ds, db)


# ── 2. List datasets ────────────────────────────────────

@router.get("/datasets")
def list_datasets(
    project_id: Optional[int] = None,
    dataset_type: Optional[str] = None,
    keyword: Optional[str] = None,
    status: str = "active",
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    q = db.query(TestDataset).filter(TestDataset.status == status)
    if project_id:
        q = q.filter(TestDataset.project_id == project_id)
    if dataset_type:
        q = q.filter(TestDataset.dataset_type == dataset_type)
    if keyword:
        q = q.filter(TestDataset.name.ilike(f"%{keyword}%"))
    total = q.count()
    datasets = q.order_by(TestDataset.updated_at.desc()).offset(offset).limit(limit).all()
    return {"data": [_serialize_dataset(ds, db) for ds in datasets], "total": total}


# ── 3. Get dataset detail ───────────────────────────────

@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    ds = db.query(TestDataset).filter(TestDataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    result = _serialize_dataset(ds, db)
    items = (
        db.query(TestDatasetItem)
        .filter(TestDatasetItem.dataset_id == dataset_id)
        .order_by(TestDatasetItem.sort_order)
        .all()
    )
    result["items"] = [_serialize_item(i) for i in items]
    bindings = db.query(TestDataBinding).filter(TestDataBinding.dataset_id == dataset_id).all()
    result["bindings"] = [
        {"id": b.id, "case_id": b.case_id, "binding_type": b.binding_type, "created_at": b.created_at.isoformat() if b.created_at else None}
        for b in bindings
    ]
    return {"data": result}


# ── 4. Update dataset ───────────────────────────────────

@router.put("/datasets/{dataset_id}")
def update_dataset(dataset_id: int, req: DatasetUpdate, db: Session = Depends(get_db)):
    ds = db.query(TestDataset).filter(TestDataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    for k, v in req.dict(exclude_unset=True).items():
        setattr(ds, k, v)
    ds.updated_at = datetime.now()
    db.commit()
    db.refresh(ds)
    return _serialize_dataset(ds, db)


# ── 5. Soft-delete dataset ──────────────────────────────

@router.delete("/datasets/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db),
    body: Optional[ConfirmRequest] = Body(None),
):
    # Phase 10B: 危险操作守卫
    check_confirm("DELETE_DATASET", (body or ConfirmRequest()).confirm, (body or ConfirmRequest()).confirm_text)
    ds = db.query(TestDataset).filter(TestDataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    ds.status = "deleted"
    ds.updated_at = datetime.now()
    db.commit()
    return {"message": "Dataset deleted", "id": dataset_id}


# ── 6. Add items to dataset ─────────────────────────────

@router.post("/datasets/{dataset_id}/items")
def add_items(dataset_id: int, req: ItemCreate, db: Session = Depends(get_db)):
    ds = db.query(TestDataset).filter(TestDataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    item = TestDatasetItem(
        dataset_id=dataset_id,
        key=req.key,
        value_json=req.value_json,
        is_sensitive=req.is_sensitive or is_sensitive_key(req.key),
        enabled=req.enabled,
        sort_order=req.sort_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _serialize_item(item)


# ── 7. Update item ──────────────────────────────────────

@router.put("/items/{item_id}")
def update_item(item_id: int, req: ItemUpdate, db: Session = Depends(get_db)):
    item = db.query(TestDatasetItem).filter(TestDatasetItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for k, v in req.dict(exclude_unset=True).items():
        setattr(item, k, v)
    if req.key and is_sensitive_key(req.key):
        item.is_sensitive = True
    item.updated_at = datetime.now()
    db.commit()
    db.refresh(item)
    return _serialize_item(item)


# ── 8. Delete item ──────────────────────────────────────

@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(TestDatasetItem).filter(TestDatasetItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Item deleted", "id": item_id}


# ── 9. Bind dataset to case ─────────────────────────────

@router.post("/bindings")
def create_binding(req: BindingCreate, db: Session = Depends(get_db)):
    ds = db.query(TestDataset).filter(TestDataset.id == req.dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    tc = db.query(TestCase).filter(TestCase.id == req.case_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="TestCase not found")
    existing = db.query(TestDataBinding).filter(
        TestDataBinding.dataset_id == req.dataset_id,
        TestDataBinding.case_id == req.case_id,
    ).first()
    if existing:
        return {"id": existing.id, "dataset_id": existing.dataset_id, "case_id": existing.case_id, "binding_type": existing.binding_type, "message": "already bound"}
    binding = TestDataBinding(
        dataset_id=req.dataset_id,
        case_id=req.case_id,
        binding_type=req.binding_type,
    )
    db.add(binding)
    db.commit()
    db.refresh(binding)
    return {"id": binding.id, "dataset_id": binding.dataset_id, "case_id": binding.case_id, "binding_type": binding.binding_type}


# ── 10. Get datasets bound to a case ────────────────────

@router.get("/cases/{case_id}/datasets")
def get_case_datasets(case_id: str, db: Session = Depends(get_db)):
    bindings = db.query(TestDataBinding).filter(TestDataBinding.case_id == case_id).all()
    result = []
    for b in bindings:
        ds = db.query(TestDataset).filter(TestDataset.id == b.dataset_id).first()
        if ds:
            d = _serialize_dataset(ds, db)
            d["binding_id"] = b.id
            d["binding_type"] = b.binding_type
            result.append(d)
    return {"data": result, "total": len(result)}


# ── 11. Unbind ───────────────────────────────────────────

@router.delete("/bindings/{binding_id}")
def delete_binding(binding_id: int, db: Session = Depends(get_db)):
    binding = db.query(TestDataBinding).filter(TestDataBinding.id == binding_id).first()
    if not binding:
        raise HTTPException(status_code=404, detail="Binding not found")
    db.delete(binding)
    db.commit()
    return {"message": "Binding deleted", "id": binding_id}


# ── 12. Variable substitution preview ───────────────────

@router.post("/substitute-preview")
def substitute_preview(req: SubstitutePreview, db: Session = Depends(get_db)):
    variables, warnings = resolve_variables(req.case_id, db)
    # mask sensitive
    masked_vars = {}
    for k, v in variables.items():
        masked_vars[k] = mask_sensitive(k, v) if is_sensitive_key(k) else v
    if req.template is not None:
        result, replaced_keys, missing_keys = substitute(req.template, variables)
        return {
            "variables": masked_vars,
            "result": result,
            "replaced_keys": replaced_keys,
            "missing_keys": missing_keys,
            "warnings": warnings,
        }
    return {"variables": masked_vars, "warnings": warnings}


# ── 13. Dataset health validation ──────────────────────

@router.post("/datasets/{dataset_id}/validate")
def validate_dataset_endpoint(dataset_id: int, db: Session = Depends(get_db)):
    result = validate_dataset(dataset_id, db)
    return result


# ── 14. Clone dataset ──────────────────────────────────

@router.post("/datasets/{dataset_id}/clone")
def clone_dataset(dataset_id: int, copy_bindings: bool = False, db: Session = Depends(get_db)):
    ds = db.query(TestDataset).filter(TestDataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    new_ds = TestDataset(
        name=f"{ds.name}-copy",
        description=ds.description,
        project_id=ds.project_id,
        dataset_type=ds.dataset_type,
        case_type=ds.case_type,
        tags=list(ds.tags or []),
    )
    db.add(new_ds)
    db.commit()
    db.refresh(new_ds)

    # 复制数据项
    items = db.query(TestDatasetItem).filter(TestDatasetItem.dataset_id == dataset_id).all()
    for item in items:
        new_item = TestDatasetItem(
            dataset_id=new_ds.id,
            key=item.key,
            value_json=item.value_json,
            is_sensitive=item.is_sensitive,
            enabled=item.enabled,
            sort_order=item.sort_order,
        )
        db.add(new_item)

    # 可选复制绑定
    bindings_copied = 0
    if copy_bindings:
        bindings = db.query(TestDataBinding).filter(TestDataBinding.dataset_id == dataset_id).all()
        for b in bindings:
            new_b = TestDataBinding(
                dataset_id=new_ds.id,
                case_id=b.case_id,
                binding_type=b.binding_type,
            )
            db.add(new_b)
            bindings_copied += 1

    db.commit()
    result = _serialize_dataset(new_ds, db)
    result["cloned_from"] = dataset_id
    result["items_copied"] = len(items)
    result["bindings_copied"] = bindings_copied
    return result


# ── 15. Cleanup run ────────────────────────────────────

@router.post("/cleanup/run")
def cleanup_run(req: CleanupRequest, db: Session = Depends(get_db)):
    result = execute_cleanup(req.dataset_id, req.case_id, req.allow_cleanup, db)
    return result

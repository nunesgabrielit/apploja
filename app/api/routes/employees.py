from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter

from app.core.dependencies import CurrentEmployeeOrAdminDep, DBSession
from app.schemas.common import ApiResponse
from app.schemas.order import EmployeePerformanceItem
from app.services.order_service import OrderService

router = APIRouter(prefix="/admin/employees", tags=["admin-employees"])


@router.get("/performance", response_model=ApiResponse[list[EmployeePerformanceItem]])
async def get_employee_performance(
    session: DBSession,
    current_user: CurrentEmployeeOrAdminDep,
) -> ApiResponse[list[EmployeePerformanceItem]]:
    performance = await OrderService(session).list_employee_performance()
    data = [
        EmployeePerformanceItem(
            employee_id=row["employee_id"],
            employee_name=row["employee_name"],
            employee_email=row["employee_email"],
            processed_orders=int(row["processed_orders"] or 0),
            assigned_orders=int(row["assigned_orders"] or 0),
            completed_orders=int(row["completed_orders"] or 0),
            total_sold=Decimal(str(row["total_sold"] or 0)),
        )
        for row in performance
    ]
    return ApiResponse[list[EmployeePerformanceItem]](
        message="Employee performance retrieved successfully",
        data=data,
    )

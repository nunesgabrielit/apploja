from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.core.dependencies import CurrentCustomerDep, DBSession
from app.schemas.address import AddressCreate, AddressRead, AddressUpdate
from app.schemas.common import ApiResponse
from app.services.address_service import AddressService

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("", response_model=ApiResponse[list[AddressRead]])
async def list_my_addresses(
    session: DBSession,
    current_user: CurrentCustomerDep,
) -> ApiResponse[list[AddressRead]]:
    addresses = await AddressService(session).list_my_addresses(current_user)
    return ApiResponse[list[AddressRead]](
        message="Addresses retrieved successfully",
        data=[AddressRead.from_model(address) for address in addresses],
    )


@router.post("", response_model=ApiResponse[AddressRead])
async def create_address(
    payload: AddressCreate,
    session: DBSession,
    current_user: CurrentCustomerDep,
) -> ApiResponse[AddressRead]:
    address = await AddressService(session).create_for_user(current_user, payload)
    return ApiResponse[AddressRead](
        message="Address created successfully",
        data=AddressRead.from_model(address),
    )


@router.put("/{address_id}", response_model=ApiResponse[AddressRead])
async def update_address(
    address_id: UUID,
    payload: AddressUpdate,
    session: DBSession,
    current_user: CurrentCustomerDep,
) -> ApiResponse[AddressRead]:
    address = await AddressService(session).update_for_user(current_user, address_id, payload)
    return ApiResponse[AddressRead](
        message="Address updated successfully",
        data=AddressRead.from_model(address),
    )


@router.delete("/{address_id}", response_model=ApiResponse[AddressRead])
async def delete_address(
    address_id: UUID,
    session: DBSession,
    current_user: CurrentCustomerDep,
) -> ApiResponse[AddressRead]:
    address = await AddressService(session).deactivate_for_user(current_user, address_id)
    return ApiResponse[AddressRead](
        message="Address deactivated successfully",
        data=AddressRead.from_model(address),
    )

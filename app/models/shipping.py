from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ShippingRule(TimestampMixin, Base):
    __tablename__ = "shipping_rules"
    __table_args__ = (
        CheckConstraint("length(zip_code_start) = 8", name="shipping_rules_zip_code_start_length"),
        CheckConstraint("length(zip_code_end) = 8", name="shipping_rules_zip_code_end_length"),
        CheckConstraint("zip_code_start <= zip_code_end", name="shipping_rules_zip_code_range_valid"),
        CheckConstraint("shipping_price >= 0", name="shipping_rules_shipping_price_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zip_code_start: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    zip_code_end: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    shipping_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    estimated_time_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)


class ShippingDistanceRule(TimestampMixin, Base):
    __tablename__ = "shipping_distance_rules"
    __table_args__ = (
        CheckConstraint("max_distance_km > 0", name="shipping_distance_rules_distance_positive"),
        CheckConstraint("shipping_price >= 0", name="shipping_distance_rules_price_non_negative"),
        CheckConstraint("sort_order >= 0", name="shipping_distance_rules_sort_order_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    max_distance_km: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, index=True)
    shipping_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    estimated_time_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)


class ShippingStoreConfig(TimestampMixin, Base):
    __tablename__ = "shipping_store_configs"
    __table_args__ = (
        CheckConstraint("length(zip_code) = 8", name="shipping_store_configs_zip_code_length"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_name: Mapped[str] = mapped_column(String(255), nullable=False, default="WM Distribuidora")
    zip_code: Mapped[str] = mapped_column(String(8), nullable=False)
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    number: Mapped[str] = mapped_column(String(50), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    complement: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

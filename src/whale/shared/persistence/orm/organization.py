"""组织模块."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from whale.shared.persistence import Base

if TYPE_CHECKING:
    from whale.shared.persistence.orm.asset import AssetInstance


class Organization(Base):
    __tablename__ = "org_unit"
    __table_args__ = {"comment": "组织（集团/大区/电场）"}

    org_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="组织名称")
    parent_org_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("org_unit.org_id"), nullable=True, index=True, comment="上级组织ID"
    )

    parent: Mapped[Optional["Organization"]] = relationship(
        back_populates="children", remote_side=[org_id]
    )
    children: Mapped[list["Organization"]] = relationship(back_populates="parent")
    asset_instances: Mapped[list["AssetInstance"]] = relationship(back_populates="org")

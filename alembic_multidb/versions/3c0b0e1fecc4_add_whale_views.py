"""add whale views

Revision ID: 3c0b0e1fecc4
Revises: eb5d458b81c8
Create Date: 2026-06-30 11:48:00.276959

"""
from typing import Sequence, Union

from alembic import op

from pacific.whale.shared.persistence.views.registry import ALL_VIEW_DEFINITIONS

# revision identifiers, used by Alembic.
revision: str = '3c0b0e1fecc4'
down_revision: Union[str, Sequence[str], None] = 'eb5d458b81c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade(engine_name: str) -> None:
    """Upgrade schema."""
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name: str) -> None:
    """Downgrade schema."""
    globals()["downgrade_%s" % engine_name]()


def upgrade_whale() -> None:
    """Upgrade whale schema."""
    dialect = op.get_context().dialect

    for view in ALL_VIEW_DEFINITIONS:
        op.execute(view.create_sql(dialect))


def downgrade_whale() -> None:
    """Downgrade whale schema."""
    for view in reversed(ALL_VIEW_DEFINITIONS):
        op.execute(view.drop_sql())


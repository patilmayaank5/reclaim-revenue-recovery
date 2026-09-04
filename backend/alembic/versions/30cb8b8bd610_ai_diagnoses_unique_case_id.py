"""ai_diagnoses_unique_case_id

Revision ID: 30cb8b8bd610
Revises: 002
Create Date: 2026-09-03 16:30:34.967432

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30cb8b8bd610'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_ai_diagnoses_case_id", "ai_diagnoses", ["case_id"])


def downgrade() -> None:
    op.drop_constraint("uq_ai_diagnoses_case_id", "ai_diagnoses", type_="unique")

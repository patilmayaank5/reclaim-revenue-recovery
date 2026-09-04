"""verification_action_unique

Revision ID: c29af7ed8887
Revises: b29af7ed8886
Create Date: 2026-09-03 19:15:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c29af7ed8887'
down_revision: Union[str, None] = 'b29af7ed8886'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unique constraint on verifications.action_id
    op.create_unique_constraint("uq_verifications_action_id", "verifications", ["action_id"])


def downgrade() -> None:
    op.drop_constraint("uq_verifications_action_id", "verifications", type_="unique")

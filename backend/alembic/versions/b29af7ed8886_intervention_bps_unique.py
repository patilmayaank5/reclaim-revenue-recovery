"""intervention_bps_unique

Revision ID: b29af7ed8886
Revises: 30cb8b8bd610
Create Date: 2026-09-03 16:42:52.222897

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b29af7ed8886'
down_revision: Union[str, None] = '30cb8b8bd610'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new column
    op.add_column("interventions", sa.Column("estimated_recovery_probability_bps", sa.Integer(), nullable=True))

    # Migrate data if any
    op.execute(
        "UPDATE interventions SET estimated_recovery_probability_bps = CAST(estimated_recovery_probability * 10000 AS INTEGER)"
    )

    # Make new column not nullable
    op.alter_column("interventions", "estimated_recovery_probability_bps", nullable=False)

    # Drop old column
    op.drop_column("interventions", "estimated_recovery_probability")

    # Add unique constraint
    op.create_unique_constraint("uq_interventions_case_id_type", "interventions", ["case_id", "intervention_type"])


def downgrade() -> None:
    op.drop_constraint("uq_interventions_case_id_type", "interventions", type_="unique")

    op.add_column("interventions", sa.Column("estimated_recovery_probability", sa.Float(), nullable=True))
    op.execute(
        "UPDATE interventions SET estimated_recovery_probability = CAST(estimated_recovery_probability_bps AS FLOAT) / 10000.0"
    )
    op.alter_column("interventions", "estimated_recovery_probability", nullable=False)
    op.drop_column("interventions", "estimated_recovery_probability_bps")

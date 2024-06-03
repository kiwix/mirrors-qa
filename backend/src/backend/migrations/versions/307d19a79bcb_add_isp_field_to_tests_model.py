"""add isp field to tests model

Revision ID: 307d19a79bcb
Revises: d45beab913d1
Create Date: 2024-06-03 12:22:41.041501

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "307d19a79bcb"
down_revision: Union[str, None] = "d45beab913d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("test", sa.Column("isp", postgresql.CITEXT(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("test", "isp")
    # ### end Alembic commands ###

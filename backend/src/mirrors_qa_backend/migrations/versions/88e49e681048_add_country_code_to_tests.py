"""add country code to tests

Revision ID: 88e49e681048
Revises: 5c376f6fb191
Create Date: 2024-06-20 21:43:32.830017

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "88e49e681048"
down_revision = "5c376f6fb191"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("test", sa.Column("country_code", sa.String(), nullable=True))
    op.create_foreign_key(
        op.f("fk_test_country_code_country"),
        "test",
        "country",
        ["country_code"],
        ["code"],
    )
    op.drop_column("test", "country")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "test", sa.Column("country", sa.VARCHAR(), autoincrement=False, nullable=True)
    )
    op.drop_constraint(op.f("fk_test_country_code_country"), "test", type_="foreignkey")
    op.drop_column("test", "country_code")
    # ### end Alembic commands ###

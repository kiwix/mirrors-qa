"""remove locations table

Revision ID: 17d587447299
Revises: 1e455d030d80
Create Date: 2024-07-17 04:39:53.486384

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "17d587447299"
down_revision = "1e455d030d80"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("location")
    op.drop_constraint("fk_mirror_country_code_country", "mirror", type_="foreignkey")
    op.drop_column("mirror", "country_code")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "mirror",
        sa.Column("country_code", sa.VARCHAR(), autoincrement=False, nullable=False),
    )
    op.create_foreign_key(
        "fk_mirror_country_code_country",
        "mirror",
        "country",
        ["country_code"],
        ["code"],
    )
    op.create_table(
        "location",
        sa.Column("code", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("code", name="pk_location"),
    )
    # ### end Alembic commands ###

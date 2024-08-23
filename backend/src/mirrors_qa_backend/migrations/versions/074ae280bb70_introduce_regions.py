"""introduce regions

Revision ID: 074ae280bb70
Revises: 17d587447299
Create Date: 2024-08-22 11:57:17.239215

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "074ae280bb70"
down_revision = "17d587447299"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "region",
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("code", name=op.f("pk_region")),
    )
    op.add_column("country", sa.Column("region_code", sa.String(), nullable=True))
    op.create_foreign_key(
        op.f("fk_country_region_code_region"),
        "country",
        "region",
        ["region_code"],
        ["code"],
    )
    op.add_column("mirror", sa.Column("region_code", sa.String(), nullable=True))
    op.add_column("mirror", sa.Column("country_code", sa.String(), nullable=True))
    op.create_foreign_key(
        op.f("fk_mirror_country_code_country"),
        "mirror",
        "country",
        ["country_code"],
        ["code"],
    )
    op.create_foreign_key(
        op.f("fk_mirror_region_code_region"),
        "mirror",
        "region",
        ["region_code"],
        ["code"],
    )
    op.drop_column("mirror", "region")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "mirror", sa.Column("region", sa.VARCHAR(), autoincrement=False, nullable=True)
    )
    op.drop_constraint(
        op.f("fk_mirror_region_code_region"), "mirror", type_="foreignkey"
    )
    op.drop_constraint(
        op.f("fk_mirror_country_code_country"), "mirror", type_="foreignkey"
    )
    op.drop_column("mirror", "country_code")
    op.drop_column("mirror", "region_code")
    op.drop_constraint(
        op.f("fk_country_region_code_region"), "country", type_="foreignkey"
    )
    op.drop_column("country", "region_code")
    op.drop_table("region")
    # ### end Alembic commands ###
"""unlink country_code from test to country

Revision ID: e1f384f65fcc
Revises: e6deb0a57a6a
Create Date: 2024-07-05 17:40:39.503348

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e1f384f65fcc"
down_revision = "e6deb0a57a6a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("fk_test_country_code_country", "test", type_="foreignkey")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key(
        "fk_test_country_code_country", "test", "country", ["country_code"], ["code"]
    )
    # ### end Alembic commands ###

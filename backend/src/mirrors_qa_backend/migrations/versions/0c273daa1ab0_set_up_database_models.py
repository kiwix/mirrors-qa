"""set up database models

Revision ID: 0c273daa1ab0
Revises:
Create Date: 2024-06-04 11:56:53.888630

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0c273daa1ab0"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "test",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("requested_on", sa.DateTime(), nullable=False),
        sa.Column("started_on", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "MISSED",
                "SUCCEEDED",
                "ERRORED",
                name="status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("isp", sa.String(), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("asn", sa.String(), nullable=True),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("latency", sa.Integer(), nullable=True),
        sa.Column("download_size", sa.Integer(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_test")),
    )
    op.create_table(
        "worker",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("pubkey_pkcs8", sa.String(), nullable=False),
        sa.Column("pubkey_fingerprint", sa.String(), nullable=False),
        sa.Column("last_seen_on", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_worker")),
    )
    op.create_table(
        "country",
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("worker_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["worker_id"], ["worker.id"], name=op.f("fk_country_worker_id_worker")
        ),
        sa.PrimaryKeyConstraint("code", name=op.f("pk_country")),
        sa.UniqueConstraint("name", "code", name=op.f("uq_country_name")),
    )
    op.create_table(
        "mirror",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("base_url", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("region", sa.String(), nullable=True),
        sa.Column("asn", sa.String(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("country_only", sa.Boolean(), nullable=True),
        sa.Column("region_only", sa.Boolean(), nullable=True),
        sa.Column("as_only", sa.Boolean(), nullable=True),
        sa.Column("other_countries", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("country_code", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["country_code"],
            ["country.code"],
            name=op.f("fk_mirror_country_code_country"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_mirror")),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("mirror")
    op.drop_table("country")
    op.drop_table("worker")
    op.drop_table("test")
    # ### end Alembic commands ###

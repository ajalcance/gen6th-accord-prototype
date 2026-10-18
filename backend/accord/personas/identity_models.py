"""Server-managed Zynth bindings to Accord identities; membership never comes from a browser."""

from uuid import UUID

from sqlalchemy import ForeignKeyConstraint, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from accord.db.base import Base


class IdentityBinding(Base):
    __tablename__ = "persona_identity_bindings"
    workspace_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    issuer: Mapped[str] = mapped_column(String(512), primary_key=True)
    subject: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    actor_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    __table_args__ = (
        UniqueConstraint("issuer", "tenant_id", "subject"),
        UniqueConstraint("workspace_id", "actor_ref"),
        ForeignKeyConstraint(
            ["workspace_id", "actor_ref"],
            ["persona_workspace_members.workspace_id", "persona_workspace_members.actor_ref"],
        ),
    )

from enum import Enum
from sqlalchemy import Index, ForeignKey, Column, Enum as SQLAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from atst.models import Base, mixins
from .types import Id

from atst.database import db
from atst.models.environment_role import EnvironmentRole
from atst.models.project import Project
from atst.models.environment import Environment


class Status(Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    PENDING = "pending"


class WorkspaceRole(Base, mixins.TimestampsMixin, mixins.AuditableMixin):
    __tablename__ = "workspace_roles"

    id = Id()
    workspace_id = Column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), index=True, nullable=False
    )
    workspace = relationship("Workspace", back_populates="roles")

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    role = relationship("Role")

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )

    status = Column(SQLAEnum(Status, native_enum=False, default=Status.PENDING))

    def __repr__(self):
        return "<WorkspaceRole(role='{}', workspace='{}', user_id='{}', id='{}')>".format(
            self.role.name, self.workspace.name, self.user_id, self.id
        )

    @property
    def latest_invitation(self):
        if self.invitations:
            return self.invitations[-1]

    @property
    def display_status(self):
        if self.status == Status.ACTIVE:
            return "Active"
        elif self.latest_invitation:
            if self.latest_invitation.is_rejected_expired:
                return "Invite expired"
            elif self.latest_invitation.is_rejected_wrong_user:
                return "Error on invite"
            elif self.latest_invitation.is_expired:
                return "Invite expired"
            else:
                return "Pending"
        else:
            return "Unknown errors"

    @property
    def has_dod_id_error(self):
        return self.latest_invitation and self.latest_invitation.is_rejected_wrong_user

    @property
    def role_name(self):
        return self.role.name

    @property
    def user_name(self):
        return self.user.full_name

    @property
    def role_displayname(self):
        return self.role.display_name

    @property
    def num_environment_roles(self):
        return (
            db.session.query(EnvironmentRole)
            .join(EnvironmentRole.environment)
            .join(Environment.project)
            .join(Project.workspace)
            .filter(Project.workspace_id == self.workspace_id)
            .filter(EnvironmentRole.user_id == self.user_id)
            .count()
        )

    @property
    def environment_roles(self):
        return (
            db.session.query(EnvironmentRole)
            .join(EnvironmentRole.environment)
            .join(Environment.project)
            .join(Project.workspace)
            .filter(Project.workspace_id == self.workspace_id)
            .filter(EnvironmentRole.user_id == self.user_id)
            .all()
        )

    @property
    def has_environment_roles(self):
        return self.num_environment_roles > 0


Index(
    "workspace_role_user_workspace",
    WorkspaceRole.user_id,
    WorkspaceRole.workspace_id,
    unique=True,
)

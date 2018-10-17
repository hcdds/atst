from atst.domain.environments import Environments
from atst.domain.environment_roles import EnvironmentRoles
from atst.domain.workspace_users import WorkspaceUsers

from tests.factories import UserFactory, WorkspaceFactory


def test_update_environment_roles():
    owner = UserFactory.create()
    developer = UserFactory.from_atat_role("developer")

    workspace = WorkspaceFactory.create(
        owner=owner,
        members=[{"user": developer, "role_name": "developer"}],
        projects=[
            {
                "name": "project1",
                "environments": [
                    {
                        "name": "project1 dev",
                        "members": [{"user": developer, "role_name": "devlops"}],
                    },
                    {
                        "name": "project1 staging",
                        "members": [{"user": developer, "role_name": "developer"}],
                    },
                    {"name": "project1 prod"},
                ],
            }
        ],
    )

    dev_env = workspace.projects[0].environments[0]
    staging_env = workspace.projects[0].environments[1]
    new_ids_and_roles = [
        {"id": dev_env.id, "role": "billing_admin"},
        {"id": staging_env.id, "role": "developer"},
    ]

    workspace_user = workspace.members[0]
    Environments.update_environment_roles(
        owner, workspace, workspace_user, new_ids_and_roles
    )
    new_dev_env_role = EnvironmentRoles.get(workspace_user.user.id, dev_env.id)
    staging_env_role = EnvironmentRoles.get(workspace_user.user.id, staging_env.id)

    assert new_dev_env_role.role == "billing_admin"
    assert staging_env_role.role == "developer"


def test_remove_environment_role():
    owner = UserFactory.create()
    developer = UserFactory.from_atat_role("developer")
    workspace = WorkspaceFactory.create(
        owner=owner,
        members=[{"user": developer, "role_name": "developer"}],
        projects=[
            {
                "name": "project1",
                "environments": [
                    {
                        "name": "project1 dev",
                        "members": [{"user": developer, "role_name": "devops"}],
                    },
                    {
                        "name": "project1 staging",
                        "members": [{"user": developer, "role_name": "developer"}],
                    },
                    {
                        "name": "project1 uat",
                        "members": [
                            {"user": developer, "role_name": "financial_auditor"}
                        ],
                    },
                    {"name": "project1 prod"},
                ],
            }
        ],
    )

    project = workspace.projects[0]
    now_ba = project.environments[0].id
    now_none = project.environments[1].id
    still_fa = project.environments[2].id

    new_environment_roles = [
        {"id": now_ba, "role": "billing_auditor"},
        {"id": now_none, "role": None},
    ]

    workspace_user = WorkspaceUsers.get(workspace.id, developer.id)
    Environments.update_environment_roles(
        owner, workspace, workspace_user, new_environment_roles
    )

    assert workspace_user.num_environment_roles == 2
    assert EnvironmentRoles.get(developer.id, now_ba).role == "billing_auditor"
    assert EnvironmentRoles.get(developer.id, now_none) is None
    assert EnvironmentRoles.get(developer.id, still_fa).role == "financial_auditor"


def test_get_scoped_environments(db):
    developer = UserFactory.create()
    workspace = WorkspaceFactory.create(
        members=[{"user": developer, "role_name": "developer"}],
        projects=[
            {
                "name": "project1",
                "environments": [
                    {
                        "name": "project1 dev",
                        "members": [{"user": developer, "role_name": "developer"}],
                    },
                    {"name": "project1 staging"},
                    {"name": "project1 prod"},
                ],
            },
            {
                "name": "project2",
                "environments": [
                    {"name": "project2 dev"},
                    {
                        "name": "project2 staging",
                        "members": [{"user": developer, "role_name": "developer"}],
                    },
                    {"name": "project2 prod"},
                ],
            },
        ],
    )

    project1_envs = Environments.for_user(developer, workspace.projects[0])
    assert [env.name for env in project1_envs] == ["project1 dev"]

    project2_envs = Environments.for_user(developer, workspace.projects[1])
    assert [env.name for env in project2_envs] == ["project2 staging"]

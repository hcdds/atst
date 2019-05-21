import pytest
from uuid import uuid4

from atst.domain.exceptions import NotFoundError, UnauthorizedError
from atst.domain.portfolios import Portfolios, PortfolioError
from atst.domain.portfolio_roles import PortfolioRoles
from atst.domain.applications import Applications
from atst.domain.environments import Environments
from atst.domain.permission_sets import PermissionSets, PORTFOLIO_PERMISSION_SETS
from atst.models.application_role import Status as ApplicationRoleStatus
from atst.models.portfolio_role import Status as PortfolioRoleStatus

from tests.factories import (
    ApplicationFactory,
    ApplicationRoleFactory,
    UserFactory,
    PortfolioRoleFactory,
    PortfolioFactory,
    get_all_portfolio_permission_sets,
)


@pytest.fixture(scope="function")
def portfolio_owner():
    return UserFactory.create()


@pytest.fixture(scope="function")
def portfolio(portfolio_owner):
    portfolio = PortfolioFactory.create(owner=portfolio_owner)
    return portfolio


def test_can_create_portfolio():
    portfolio = PortfolioFactory.create(name="frugal-whale")
    assert portfolio.name == "frugal-whale"


def test_get_nonexistent_portfolio_raises():
    with pytest.raises(NotFoundError):
        Portfolios.get(UserFactory.build(), uuid4())


def test_creating_portfolio_adds_owner(portfolio, portfolio_owner):
    assert portfolio.roles[0].user == portfolio_owner


def test_portfolio_has_timestamps(portfolio):
    assert portfolio.time_created == portfolio.time_updated


def test_can_create_portfolio_role(portfolio, portfolio_owner):
    user_data = {
        "first_name": "New",
        "last_name": "User",
        "email": "new.user@mail.com",
        "portfolio_role": "developer",
        "dod_id": "1234567890",
    }

    new_member = Portfolios.create_member(portfolio, user_data)
    assert new_member.portfolio == portfolio
    assert new_member.user.provisional


def test_can_add_existing_user_to_portfolio(portfolio, portfolio_owner):
    user = UserFactory.create()
    user_data = {
        "first_name": "New",
        "last_name": "User",
        "email": "new.user@mail.com",
        "portfolio_role": "developer",
        "dod_id": user.dod_id,
    }

    new_member = Portfolios.create_member(portfolio, user_data)
    assert new_member.portfolio == portfolio
    assert new_member.user.email == user.email
    assert not new_member.user.provisional


def test_update_portfolio_role_role(portfolio, portfolio_owner):
    user_data = {
        "first_name": "New",
        "last_name": "User",
        "email": "new.user@mail.com",
        "portfolio_role": "developer",
        "dod_id": "1234567890",
    }
    PortfolioRoleFactory._meta.sqlalchemy_session_persistence = "flush"
    member = PortfolioRoleFactory.create(portfolio=portfolio)
    permission_sets = [PermissionSets.EDIT_PORTFOLIO_FUNDING]

    updated_member = Portfolios.update_member(member, permission_sets=permission_sets)
    assert updated_member.portfolio == portfolio


def test_scoped_portfolio_for_admin_missing_view_apps_perms(portfolio_owner, portfolio):
    Applications.create(
        portfolio, "My Application 2", "My application 2", ["dev", "staging", "prod"]
    )
    restricted_admin = UserFactory.create()
    PortfolioRoleFactory.create(
        portfolio=portfolio,
        user=restricted_admin,
        permission_sets=[PermissionSets.get(PermissionSets.VIEW_PORTFOLIO)],
    )
    scoped_portfolio = Portfolios.get(restricted_admin, portfolio.id)
    assert scoped_portfolio.id == portfolio.id
    assert len(portfolio.applications) == 1
    assert len(scoped_portfolio.applications) == 0


@pytest.mark.skip(reason="should be reworked pending application member changes")
def test_scoped_portfolio_only_returns_a_users_applications_and_environments(
    portfolio, portfolio_owner
):
    new_application = Applications.create(
        portfolio, "My Application", "My application", ["dev", "staging", "prod"]
    )
    Applications.create(
        portfolio, "My Application 2", "My application 2", ["dev", "staging", "prod"]
    )
    developer = UserFactory.create()
    dev_environment = Environments.add_member(
        new_application.environments[0], developer, "developer"
    )

    scoped_portfolio = Portfolios.get(developer, portfolio.id)

    # Should only return the application and environment in which the user has an
    # environment role.
    assert scoped_portfolio.applications == [new_application]
    assert scoped_portfolio.applications[0].environments == [dev_environment]


def test_scoped_portfolio_returns_all_applications_for_portfolio_admin(
    portfolio, portfolio_owner
):
    for _ in range(5):
        Applications.create(
            portfolio, "My Application", "My application", ["dev", "staging", "prod"]
        )

    admin = UserFactory.create()
    perm_sets = get_all_portfolio_permission_sets()
    PortfolioRoleFactory.create(
        user=admin, portfolio=portfolio, permission_sets=perm_sets
    )
    scoped_portfolio = Portfolios.get(admin, portfolio.id)

    assert len(scoped_portfolio.applications) == 5
    assert len(scoped_portfolio.applications[0].environments) == 3


def test_scoped_portfolio_returns_all_applications_for_portfolio_owner(
    portfolio, portfolio_owner
):
    for _ in range(5):
        Applications.create(
            portfolio, "My Application", "My application", ["dev", "staging", "prod"]
        )

    scoped_portfolio = Portfolios.get(portfolio_owner, portfolio.id)

    assert len(scoped_portfolio.applications) == 5
    assert len(scoped_portfolio.applications[0].environments) == 3


def test_for_user_returns_portfolios_for_applications_user_invited_to():
    bob = UserFactory.create()
    portfolio = PortfolioFactory.create()
    application = ApplicationFactory.create(portfolio=portfolio)
    ApplicationRoleFactory.create(
        application=application, user=bob, status=ApplicationRoleStatus.ACTIVE
    )

    assert portfolio in Portfolios.for_user(user=bob)


def test_for_user_returns_active_portfolios_for_user(portfolio, portfolio_owner):
    bob = UserFactory.create()
    PortfolioRoleFactory.create(
        user=bob, portfolio=portfolio, status=PortfolioRoleStatus.ACTIVE
    )
    PortfolioFactory.create()

    bobs_portfolios = Portfolios.for_user(bob)

    assert len(bobs_portfolios) == 1


def test_for_user_does_not_return_inactive_portfolios(portfolio, portfolio_owner):
    bob = UserFactory.create()
    Portfolios.add_member(portfolio, bob)
    PortfolioFactory.create()
    bobs_portfolios = Portfolios.for_user(bob)

    assert len(bobs_portfolios) == 0


def test_for_user_returns_all_portfolios_for_ccpo(portfolio, portfolio_owner):
    sam = UserFactory.create_ccpo()
    PortfolioFactory.create()

    sams_portfolios = Portfolios.for_user(sam)
    assert len(sams_portfolios) == 2


def test_can_create_portfolios_with_matching_names():
    portfolio_name = "Great Portfolio"
    PortfolioFactory.create(name=portfolio_name)
    PortfolioFactory.create(name=portfolio_name)


def test_able_to_revoke_portfolio_access_for_active_member():
    portfolio = PortfolioFactory.create()
    portfolio_role = PortfolioRoleFactory.create(
        portfolio=portfolio, status=PortfolioRoleStatus.ACTIVE
    )
    Portfolios.revoke_access(portfolio.id, portfolio_role.id)
    assert Portfolios.for_user(portfolio_role.user) == []


def test_can_revoke_access():
    portfolio = PortfolioFactory.create()
    owner_role = portfolio.roles[0]
    portfolio_role = PortfolioRoleFactory.create(
        portfolio=portfolio, status=PortfolioRoleStatus.ACTIVE
    )

    assert Portfolios.can_revoke_access_for(portfolio, portfolio_role)
    assert not Portfolios.can_revoke_access_for(portfolio, owner_role)


def test_unable_to_revoke_owner_portfolio_access():
    portfolio = PortfolioFactory.create()
    owner_portfolio_role = portfolio.roles[0]

    with pytest.raises(PortfolioError):
        Portfolios.revoke_access(portfolio.id, owner_portfolio_role.id)


def test_disabled_members_dont_show_up(session):
    portfolio = PortfolioFactory.create()
    PortfolioRoleFactory.create(portfolio=portfolio, status=PortfolioRoleStatus.ACTIVE)
    PortfolioRoleFactory.create(
        portfolio=portfolio, status=PortfolioRoleStatus.DISABLED
    )

    # should only return portfolio owner and ACTIVE member
    assert len(portfolio.members) == 2


def test_does_not_count_disabled_members(session):
    portfolio = PortfolioFactory.create()
    PortfolioRoleFactory.create(portfolio=portfolio, status=PortfolioRoleStatus.ACTIVE)
    PortfolioRoleFactory.create(portfolio=portfolio)
    PortfolioRoleFactory.create(
        portfolio=portfolio, status=PortfolioRoleStatus.DISABLED
    )

    assert portfolio.user_count == 3

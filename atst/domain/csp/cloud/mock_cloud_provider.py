from uuid import uuid4

from atst.domain.csp.cloud.exceptions import (
    BaselineProvisionException,
    EnvironmentCreationException,
    GeneralCSPException,
    UserProvisioningException,
    UserRemovalException,
)
from atst.domain.csp.cloud.models import BillingProfileTenantAccessCSPResult

from .cloud_provider_interface import CloudProviderInterface
from .exceptions import (
    AuthenticationException,
    AuthorizationException,
    ConnectionException,
    UnknownServerException,
)
from .models import (
    AZURE_MGMNT_PATH,
    ApplicationCSPPayload,
    ApplicationCSPResult,
    BillingInstructionCSPPayload,
    BillingInstructionCSPResult,
    BillingProfileCreationCSPPayload,
    BillingProfileCreationCSPResult,
    BillingProfileVerificationCSPPayload,
    BillingProfileVerificationCSPResult,
    ProductPurchaseCSPPayload,
    ProductPurchaseCSPResult,
    ProductPurchaseVerificationCSPPayload,
    ProductPurchaseVerificationCSPResult,
    TaskOrderBillingCreationCSPPayload,
    TaskOrderBillingCreationCSPResult,
    TaskOrderBillingVerificationCSPPayload,
    TaskOrderBillingVerificationCSPResult,
    TenantCSPPayload,
    TenantCSPResult,
)


class MockCloudProvider(CloudProviderInterface):

    # TODO: All of these constants
    AUTHENTICATION_EXCEPTION = AuthenticationException("Authentication failure.")
    AUTHORIZATION_EXCEPTION = AuthorizationException("Not authorized.")
    NETWORK_EXCEPTION = ConnectionException("Network failure.")
    SERVER_EXCEPTION = UnknownServerException("Not our fault.")

    SERVER_FAILURE_PCT = 1
    NETWORK_FAILURE_PCT = 7
    ENV_CREATE_FAILURE_PCT = 12
    ATAT_ADMIN_CREATE_FAILURE_PCT = 12
    UNAUTHORIZED_RATE = 2

    def __init__(
        self, config, with_delay=True, with_failure=True, with_authorization=True
    ):
        from time import sleep
        import random

        self._with_delay = with_delay
        self._with_failure = with_failure
        self._with_authorization = with_authorization
        self._sleep = sleep
        self._random = random

    def root_creds(self):
        return self._auth_credentials

    def set_secret(self, secret_key: str, secret_value: str):
        pass

    def get_secret(self, secret_key: str, default=dict()):
        return default

    def create_environment(self, auth_credentials, user, environment):
        self._authorize(auth_credentials)

        self._delay(1, 5)
        self._maybe_raise(self.NETWORK_FAILURE_PCT, self.NETWORK_EXCEPTION)
        self._maybe_raise(self.SERVER_FAILURE_PCT, self.SERVER_EXCEPTION)
        self._maybe_raise(
            self.ENV_CREATE_FAILURE_PCT,
            EnvironmentCreationException(
                environment.id, "Could not create environment."
            ),
        )

        csp_environment_id = self._id()

        self._delay(1, 5)
        self._maybe_raise(self.NETWORK_FAILURE_PCT, self.NETWORK_EXCEPTION)
        self._maybe_raise(self.SERVER_FAILURE_PCT, self.SERVER_EXCEPTION)
        self._maybe_raise(
            self.ATAT_ADMIN_CREATE_FAILURE_PCT,
            BaselineProvisionException(
                csp_environment_id, "Could not create environment baseline."
            ),
        )
        self._maybe_raise(self.UNAUTHORIZED_RATE, self.AUTHORIZATION_EXCEPTION)

        return csp_environment_id

    def create_atat_admin_user(self, auth_credentials, csp_environment_id):
        self._authorize(auth_credentials)

        self._delay(1, 5)
        self._maybe_raise(self.NETWORK_FAILURE_PCT, self.NETWORK_EXCEPTION)
        self._maybe_raise(self.SERVER_FAILURE_PCT, self.SERVER_EXCEPTION)
        self._maybe_raise(
            self.ATAT_ADMIN_CREATE_FAILURE_PCT,
            UserProvisioningException(
                csp_environment_id, "atat_admin", "Could not create admin user."
            ),
        )

        self._maybe_raise(self.UNAUTHORIZED_RATE, self.AUTHORIZATION_EXCEPTION)

        return {"id": self._id(), "credentials": self._auth_credentials}

    def create_tenant(self, payload: TenantCSPPayload):
        """
        payload is an instance of TenantCSPPayload data class
        """

        self._authorize(payload.creds)

        self._delay(1, 5)

        self._maybe_raise(self.NETWORK_FAILURE_PCT, self.NETWORK_EXCEPTION)
        self._maybe_raise(self.SERVER_FAILURE_PCT, self.SERVER_EXCEPTION)
        self._maybe_raise(self.UNAUTHORIZED_RATE, self.AUTHORIZATION_EXCEPTION)

        return TenantCSPResult(
            **{
                "tenant_id": "",
                "user_id": "",
                "user_object_id": "",
                "tenant_admin_username": "test",
                "tenant_admin_password": "test",
            }
        )

    def create_billing_profile_creation(
        self, payload: BillingProfileCreationCSPPayload
    ):
        # response will be mostly the same as the body, but we only really care about the id
        self._maybe_raise(self.NETWORK_FAILURE_PCT, self.NETWORK_EXCEPTION)
        self._maybe_raise(self.SERVER_FAILURE_PCT, self.SERVER_EXCEPTION)
        self._maybe_raise(self.UNAUTHORIZED_RATE, self.AUTHORIZATION_EXCEPTION)

        return BillingProfileCreationCSPResult(
            **dict(
                billing_profile_verify_url="https://zombo.com",
                billing_profile_retry_after=10,
            )
        )

    def create_billing_profile_verification(
        self, payload: BillingProfileVerificationCSPPayload
    ):
        self._maybe_raise(self.NETWORK_FAILURE_PCT, self.NETWORK_EXCEPTION)
        self._maybe_raise(self.SERVER_FAILURE_PCT, self.SERVER_EXCEPTION)
        self._maybe_raise(self.UNAUTHORIZED_RATE, self.AUTHORIZATION_EXCEPTION)
        return BillingProfileVerificationCSPResult(
            **{
                "id": "/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/billingProfiles/KQWI-W2SU-BG7-TGB",
                "name": "KQWI-W2SU-BG7-TGB",
                "properties": {
                    "address": {
                        "addressLine1": "123 S Broad Street, Suite 2400",
                        "city": "Philadelphia",
                        "companyName": "Promptworks",
                        "country": "US",
                        "postalCode": "19109",
                        "region": "PA",
                    },
                    "currency": "USD",
                    "displayName": "Test Billing Profile",
                    "enabledAzurePlans": [],
                    "hasReadAccess": True,
                    "invoiceDay": 5,
                    "invoiceEmailOptIn": False,
                    "invoiceSections": [
                        {
                            "id": "/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/billingProfiles/KQWI-W2SU-BG7-TGB/invoiceSections/CHCO-BAAR-PJA-TGB",
                            "name": "CHCO-BAAR-PJA-TGB",
                            "properties": {"displayName": "Test Billing Profile"},
                            "type": "Microsoft.Billing/billingAccounts/billingProfiles/invoiceSections",
                        }
                    ],
                },
                "type": "Microsoft.Billing/billingAccounts/billingProfiles",
            }
        )

    def create_billing_profile_tenant_access(self, payload):
        self._maybe_raise(self.NETWORK_FAILURE_PCT, self.NETWORK_EXCEPTION)
        self._maybe_raise(self.SERVER_FAILURE_PCT, self.SERVER_EXCEPTION)
        self._maybe_raise(self.UNAUTHORIZED_RATE, self.AUTHORIZATION_EXCEPTION)

        return BillingProfileTenantAccessCSPResult(
            **{
                "id": "/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/billingProfiles/KQWI-W2SU-BG7-TGB/billingRoleAssignments/40000000-aaaa-bbbb-cccc-100000000000_0a5f4926-e3ee-4f47-a6e3-8b0a30a40e3d",
                "name": "40000000-aaaa-bbbb-cccc-100000000000_0a5f4926-e3ee-4f47-a6e3-8b0a30a40e3d",
                "properties": {
                    "createdOn": "2020-01-14T14:39:26.3342192+00:00",
                    "createdByPrincipalId": "82e2b376-3297-4096-8743-ed65b3be0b03",
                    "principalId": "0a5f4926-e3ee-4f47-a6e3-8b0a30a40e3d",
                    "principalTenantId": "60ff9d34-82bf-4f21-b565-308ef0533435",
                    "roleDefinitionId": "/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/billingProfiles/KQWI-W2SU-BG7-TGB/billingRoleDefinitions/40000000-aaaa-bbbb-cccc-100000000000",
                    "scope": "/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/billingProfiles/KQWI-W2SU-BG7-TGB",
                },
                "type": "Microsoft.Billing/billingRoleAssignments",
            }
        )

    def create_task_order_billing_creation(
        self, payload: TaskOrderBillingCreationCSPPayload
    ):
        self._maybe_raise(self.NETWORK_FAILURE_PCT, self.NETWORK_EXCEPTION)
        self._maybe_raise(self.SERVER_FAILURE_PCT, self.SERVER_EXCEPTION)
        self._maybe_raise(self.UNAUTHORIZED_RATE, self.AUTHORIZATION_EXCEPTION)

        return TaskOrderBillingCreationCSPResult(
            **{"Location": "https://somelocation", "Retry-After": "10"}
        )

    def create_task_order_billing_verification(
        self, payload: TaskOrderBillingVerificationCSPPayload
    ):
        self._maybe_raise(self.NETWORK_FAILURE_PCT, self.NETWORK_EXCEPTION)
        self._maybe_raise(self.SERVER_FAILURE_PCT, self.SERVER_EXCEPTION)
        self._maybe_raise(self.UNAUTHORIZED_RATE, self.AUTHORIZATION_EXCEPTION)

        return TaskOrderBillingVerificationCSPResult(
            **{
                "id": "/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/billingProfiles/XC36-GRNZ-BG7-TGB",
                "name": "XC36-GRNZ-BG7-TGB",
                "properties": {
                    "address": {
                        "addressLine1": "123 S Broad Street, Suite 2400",
                        "city": "Philadelphia",
                        "companyName": "Promptworks",
                        "country": "US",
                        "postalCode": "19109",
                        "region": "PA",
                    },
                    "currency": "USD",
                    "displayName": "First Portfolio Billing Profile",
                    "enabledAzurePlans": [
                        {
                            "productId": "DZH318Z0BPS6",
                            "skuId": "0001",
                            "skuDescription": "Microsoft Azure Plan",
                        }
                    ],
                    "hasReadAccess": True,
                    "invoiceDay": 5,
                    "invoiceEmailOptIn": False,
                },
                "type": "Microsoft.Billing/billingAccounts/billingProfiles",
            }
        )

    def create_billing_instruction(self, payload: BillingInstructionCSPPayload):
        self._maybe_raise(self.NETWORK_FAILURE_PCT, self.NETWORK_EXCEPTION)
        self._maybe_raise(self.SERVER_FAILURE_PCT, self.SERVER_EXCEPTION)
        self._maybe_raise(self.UNAUTHORIZED_RATE, self.AUTHORIZATION_EXCEPTION)

        return BillingInstructionCSPResult(
            **{
                "name": "TO1:CLIN001",
                "properties": {
                    "amount": 1000.0,
                    "endDate": "2020-03-01T00:00:00+00:00",
                    "startDate": "2020-01-01T00:00:00+00:00",
                },
                "type": "Microsoft.Billing/billingAccounts/billingProfiles/billingInstructions",
            }
        )


    def create_product_purchase(self, payload: ProductPurchaseCSPPayload):
        self._maybe_raise(self.NETWORK_FAILURE_PCT, self.NETWORK_EXCEPTION)
        self._maybe_raise(self.SERVER_FAILURE_PCT, self.SERVER_EXCEPTION)
        self._maybe_raise(self.UNAUTHORIZED_RATE, self.AUTHORIZATION_EXCEPTION)

        return ProductPurchaseCSPResult(
            **{
                "name": "TO1:CLIN001",
                "properties": {
                    "amount": 1000.0,
                    "endDate": "2020-03-01T00:00:00+00:00",
                    "startDate": "2020-01-01T00:00:00+00:00",
                },
                "type": "Microsoft.Billing/billingAccounts/billingProfiles/billingInstructions",
            }
        )

    def create_product_purchase_verification(
        self, payload: ProductPurchaseVerificationCSPPayload
    ):
        self._maybe_raise(self.NETWORK_FAILURE_PCT, self.NETWORK_EXCEPTION)
        self._maybe_raise(self.SERVER_FAILURE_PCT, self.SERVER_EXCEPTION)
        self._maybe_raise(self.UNAUTHORIZED_RATE, self.AUTHORIZATION_EXCEPTION)

        return ProductPurchaseVerificationCSPResult(
            **{
            }
        )


    def create_or_update_user(self, auth_credentials, user_info, csp_role_id):
        self._authorize(auth_credentials)

        self._delay(1, 5)
        self._maybe_raise(self.NETWORK_FAILURE_PCT, self.NETWORK_EXCEPTION)
        self._maybe_raise(self.SERVER_FAILURE_PCT, self.SERVER_EXCEPTION)
        self._maybe_raise(
            self.ATAT_ADMIN_CREATE_FAILURE_PCT,
            UserProvisioningException(
                user_info.environment.id,
                user_info.application_role.user_id,
                "Could not create user.",
            ),
        )

        self._maybe_raise(self.UNAUTHORIZED_RATE, self.AUTHORIZATION_EXCEPTION)
        return self._id()

    def disable_user(self, auth_credentials, csp_user_id):
        self._authorize(auth_credentials)
        self._maybe_raise(self.NETWORK_FAILURE_PCT, self.NETWORK_EXCEPTION)
        self._maybe_raise(self.SERVER_FAILURE_PCT, self.SERVER_EXCEPTION)

        self._maybe_raise(
            self.ATAT_ADMIN_CREATE_FAILURE_PCT,
            UserRemovalException(csp_user_id, "Could not disable user."),
        )

        return self._maybe(12)

    def create_subscription(self, environment):
        self._maybe_raise(self.UNAUTHORIZED_RATE, GeneralCSPException)

        return True

    def get_calculator_url(self):
        return "https://www.rackspace.com/en-us/calculator"

    def get_environment_login_url(self, environment):
        """Returns the login url for a given environment
        """
        return "https://www.mycloud.com/my-env-login"

    def _id(self):
        return uuid4().hex

    def _delay(self, min_secs, max_secs):
        if self._with_delay:
            duration = self._random.randrange(min_secs, max_secs)
            self._sleep(duration)

    def _maybe(self, pct):
        return not self._with_failure or self._random.randrange(0, 100) < pct

    def _maybe_raise(self, pct, exc):
        if self._with_failure and self._maybe(pct):
            raise exc

    @property
    def _auth_credentials(self):
        return {"username": "mock-cloud", "password": "shh"}  # pragma: allowlist secret

    def _authorize(self, credentials):
        self._delay(1, 5)
        if self._with_authorization and credentials != self._auth_credentials:
            raise self.AUTHENTICATION_EXCEPTION

    def create_application(self, payload: ApplicationCSPPayload):
        self._maybe_raise(self.UNAUTHORIZED_RATE, GeneralCSPException)

        id_ = f"{AZURE_MGMNT_PATH}{payload.management_group_name}"
        return ApplicationCSPResult(id=id_)

    def get_credentials(self, scope="portfolio", tenant_id=None):
        return self.root_creds()

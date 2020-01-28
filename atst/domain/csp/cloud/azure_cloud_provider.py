import re
from secrets import token_urlsafe
from typing import Dict
from uuid import uuid4

from .cloud_provider_interface import CloudProviderInterface
from .exceptions import AuthenticationException
from .models import (
    ApplicationCSPPayload,
    ApplicationCSPResult,
    BillingInstructionCSPPayload,
    BillingInstructionCSPResult,
    BillingProfileCreationCSPPayload,
    BillingProfileCreationCSPResult,
    BillingProfileTenantAccessCSPPayload,
    BillingProfileTenantAccessCSPResult,
    BillingProfileVerificationCSPPayload,
    BillingProfileVerificationCSPResult,
    ManagementGroupCSPResponse,
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
from .policy import AzurePolicyManager

AZURE_ENVIRONMENT = "AZURE_PUBLIC_CLOUD"  # TBD
AZURE_SKU_ID = "?"  # probably a static sku specific to ATAT/JEDI
SUBSCRIPTION_ID_REGEX = re.compile(
    "subscriptions\/([0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})",
    re.I,
)

# This needs to be a fully pathed role definition identifier, not just a UUID
REMOTE_ROOT_ROLE_DEF_ID = "/providers/Microsoft.Authorization/roleDefinitions/00000000-0000-4000-8000-000000000000"
AZURE_MANAGEMENT_API = "https://management.azure.com"


class AzureSDKProvider(object):
    def __init__(self):
        from azure.mgmt import subscription, authorization, managementgroups
        from azure.mgmt.resource import policy
        import azure.graphrbac as graphrbac
        import azure.common.credentials as credentials
        import azure.identity as identity
        from azure.keyvault import secrets
        from azure.core import exceptions

        from msrestazure.azure_cloud import AZURE_PUBLIC_CLOUD
        import adal
        import requests

        self.subscription = subscription
        self.policy = policy
        self.managementgroups = managementgroups
        self.authorization = authorization
        self.adal = adal
        self.graphrbac = graphrbac
        self.credentials = credentials
        self.identity = identity
        self.exceptions = exceptions
        self.secrets = secrets
        self.requests = requests
        # may change to a JEDI cloud
        self.cloud = AZURE_PUBLIC_CLOUD


class AzureCloudProvider(CloudProviderInterface):
    def __init__(self, config, azure_sdk_provider=None):
        self.config = config

        self.client_id = config["AZURE_CLIENT_ID"]
        self.secret_key = config["AZURE_SECRET_KEY"]
        self.tenant_id = config["AZURE_TENANT_ID"]
        self.vault_url = config["AZURE_VAULT_URL"]

        if azure_sdk_provider is None:
            self.sdk = AzureSDKProvider()
        else:
            self.sdk = azure_sdk_provider

        self.policy_manager = AzurePolicyManager(config["AZURE_POLICY_LOCATION"])

    def set_secret(self, secret_key, secret_value):
        credential = self._get_client_secret_credential_obj({})
        secret_client = self.secrets.SecretClient(
            vault_url=self.vault_url, credential=credential,
        )
        try:
            return secret_client.set_secret(secret_key, secret_value)
        except self.exceptions.HttpResponseError:
            app.logger.error(
                f"Could not SET secret in Azure keyvault for key {secret_key}.",
                exc_info=1,
            )

    def get_secret(self, secret_key):
        credential = self._get_client_secret_credential_obj({})
        secret_client = self.secrets.SecretClient(
            vault_url=self.vault_url, credential=credential,
        )
        try:
            return secret_client.get_secret(secret_key).value
        except self.exceptions.HttpResponseError:
            app.logger.error(
                f"Could not GET secret in Azure keyvault for key {secret_key}.",
                exc_info=1,
            )

    def create_environment(self, auth_credentials: Dict, user, environment):
        # since this operation would only occur within a tenant, should we source the tenant
        # via lookup from environment once we've created the portfolio csp data schema
        # something like this:
        # environment_tenant = environment.application.portfolio.csp_data.get('tenant_id', None)
        # though we'd probably source the whole credentials for these calls from the portfolio csp
        # data, as it would have to be where we store the creds for the at-at user within the portfolio tenant
        # credentials = self._get_credential_obj(environment.application.portfolio.csp_data.get_creds())
        credentials = self._get_credential_obj(self._root_creds)
        display_name = f"{environment.application.name}_{environment.name}_{environment.id}"  # proposed format
        management_group_id = "?"  # management group id chained from environment
        parent_id = "?"  # from environment.application

        management_group = self._create_management_group(
            credentials, management_group_id, display_name, parent_id,
        )

        return ManagementGroupCSPResponse(**management_group)

    def create_atat_admin_user(
        self, auth_credentials: Dict, csp_environment_id: str
    ) -> Dict:
        root_creds = self._root_creds
        credentials = self._get_credential_obj(root_creds)

        sub_client = self.sdk.subscription.SubscriptionClient(credentials)
        subscription = sub_client.subscriptions.get(csp_environment_id)

        managment_principal = self._get_management_service_principal()

        auth_client = self.sdk.authorization.AuthorizationManagementClient(
            credentials,
            # TODO: Determine which subscription this needs to point at
            # Once we're in a multi-sub environment
            subscription.id,
        )

        # Create role assignment for
        role_assignment_id = str(uuid4())
        role_assignment_create_params = auth_client.role_assignments.models.RoleAssignmentCreateParameters(
            role_definition_id=REMOTE_ROOT_ROLE_DEF_ID,
            principal_id=managment_principal.id,
        )

        auth_client.role_assignments.create(
            scope=f"/subscriptions/{subscription.id}/",
            role_assignment_name=role_assignment_id,
            parameters=role_assignment_create_params,
        )

        return {
            "csp_user_id": managment_principal.object_id,
            "credentials": managment_principal.password_credentials,
            "role_name": role_assignment_id,
        }

    def create_application(self, payload: ApplicationCSPPayload):
        creds = payload.creds
        credentials = self._get_credential_obj(creds, resource=AZURE_MANAGEMENT_API)

        response = self._create_management_group(
            credentials,
            payload.management_group_name,
            payload.display_name,
            payload.parent_id,
        )

        return ApplicationCSPResult(**response)

    def _create_management_group(
        self, credentials, management_group_id, display_name, parent_id=None,
    ):
        mgmgt_group_client = self.sdk.managementgroups.ManagementGroupsAPI(credentials)
        create_parent_grp_info = self.sdk.managementgroups.models.CreateParentGroupInfo(
            id=parent_id
        )
        create_mgmt_grp_details = self.sdk.managementgroups.models.CreateManagementGroupDetails(
            parent=create_parent_grp_info
        )
        mgmt_grp_create = self.sdk.managementgroups.models.CreateManagementGroupRequest(
            name=management_group_id,
            display_name=display_name,
            details=create_mgmt_grp_details,
        )
        create_request = mgmgt_group_client.management_groups.create_or_update(
            management_group_id, mgmt_grp_create
        )

        # result is a synchronous wait, might need to do a poll instead to handle first mgmt group create
        # since we were told it could take 10+ minutes to complete, unless this handles that polling internally
        # TODO: what to do is status is not 'Succeeded' on the
        # response object? Will it always raise its own error
        # instead?
        return create_request.result()

    def _create_subscription(
        self,
        credentials,
        display_name,
        billing_profile_id,
        sku_id,
        management_group_id,
        billing_account_name,
        invoice_section_name,
    ):
        sub_client = self.sdk.subscription.SubscriptionClient(credentials)

        billing_profile_id = "?"  # where do we source this?
        sku_id = AZURE_SKU_ID
        # These 2 seem like something that might be worthwhile to allow tiebacks to
        # TOs filed for the environment
        billing_account_name = "?"  # from TO?
        invoice_section_name = "?"  # from TO?

        body = self.sdk.subscription.models.ModernSubscriptionCreationParameters(
            display_name=display_name,
            billing_profile_id=billing_profile_id,
            sku_id=sku_id,
            management_group_id=management_group_id,
        )

        # We may also want to create billing sections in the enrollment account
        sub_creation_operation = sub_client.subscription_factory.create_subscription(
            billing_account_name, invoice_section_name, body
        )

        # the resulting object from this process is a link to the new subscription
        # not a subscription model, so we'll have to unpack the ID
        new_sub = sub_creation_operation.result()

        subscription_id = self._extract_subscription_id(new_sub.subscription_link)
        if subscription_id:
            return subscription_id
        else:
            # troublesome error, subscription should exist at this point
            # but we just don't have a valid ID
            pass

    def _create_policy_definition(
        self, credentials, subscription_id, management_group_id, properties,
    ):
        """
        Requires credentials that have AZURE_MANAGEMENT_API
        specified as the resource. The Service Principal
        specified in the credentials must have the "Resource
        Policy Contributor" role assigned with a scope at least
        as high as the management group specified by
        management_group_id.

        Arguments:
            credentials -- ServicePrincipalCredentials
            subscription_id -- str, ID of the subscription (just the UUID, not the path)
            management_group_id -- str, ID of the management group (just the UUID, not the path)
            properties -- dictionary, the "properties" section of a valid Azure policy definition document

        Returns:
            azure.mgmt.resource.policy.[api version].models.PolicyDefinition: the PolicyDefinition object provided to Azure

        Raises:
            TBD
        """
        # TODO: which subscription would this be?
        client = self.sdk.policy.PolicyClient(credentials, subscription_id)

        definition = client.policy_definitions.models.PolicyDefinition(
            policy_type=properties.get("policyType"),
            mode=properties.get("mode"),
            display_name=properties.get("displayName"),
            description=properties.get("description"),
            policy_rule=properties.get("policyRule"),
            parameters=properties.get("parameters"),
        )

        name = properties.get("displayName")

        return client.policy_definitions.create_or_update_at_management_group(
            policy_definition_name=name,
            parameters=definition,
            management_group_id=management_group_id,
        )

    def create_tenant(self, payload: TenantCSPPayload):
        sp_token = self._get_sp_token(payload.creds)
        if sp_token is None:
            raise AuthenticationException("Could not resolve token for tenant creation")

        payload.password = token_urlsafe(16)
        create_tenant_body = payload.dict(by_alias=True)

        create_tenant_headers = {
            "Authorization": f"Bearer {sp_token}",
        }

        result = self.sdk.requests.post(
            "https://management.azure.com/providers/Microsoft.SignUp/createTenant?api-version=2020-01-01-preview",
            json=create_tenant_body,
            headers=create_tenant_headers,
        )

        if result.status_code == 200:
            return self._ok(
                TenantCSPResult(
                    **result.json(),
                    tenant_admin_password=payload.password,
                    tenant_admin_username=payload.user_id,
                )
            )
        else:
            return self._error(result.json())

    def create_billing_profile_creation(
        self, payload: BillingProfileCreationCSPPayload
    ):
        sp_token = self._get_sp_token(payload.creds)
        if sp_token is None:
            raise AuthenticationException(
                "Could not resolve token for billing profile creation"
            )

        create_billing_account_body = payload.dict(by_alias=True)

        create_billing_account_headers = {
            "Authorization": f"Bearer {sp_token}",
        }

        billing_account_create_url = f"https://management.azure.com/providers/Microsoft.Billing/billingAccounts/{payload.billing_account_name}/billingProfiles?api-version=2019-10-01-preview"

        result = self.sdk.requests.post(
            billing_account_create_url,
            json=create_billing_account_body,
            headers=create_billing_account_headers,
        )

        if result.status_code == 202:
            # 202 has location/retry after headers
            return self._ok(BillingProfileCreationCSPResult(**result.headers))
        elif result.status_code == 200:
            # NB: Swagger docs imply call can sometimes resolve immediately
            return self._ok(BillingProfileVerificationCSPResult(**result.json()))
        else:
            return self._error(result.json())

    def create_billing_profile_verification(
        self, payload: BillingProfileVerificationCSPPayload
    ):
        sp_token = self._get_sp_token(payload.creds)
        if sp_token is None:
            raise AuthenticationException(
                "Could not resolve token for billing profile validation"
            )

        auth_header = {
            "Authorization": f"Bearer {sp_token}",
        }

        result = self.sdk.requests.get(
            payload.billing_profile_verify_url, headers=auth_header
        )

        if result.status_code == 202:
            # 202 has location/retry after headers
            return self._ok(BillingProfileCreationCSPResult(**result.headers))
        elif result.status_code == 200:
            return self._ok(BillingProfileVerificationCSPResult(**result.json()))
        else:
            return self._error(result.json())

    def create_billing_profile_tenant_access(
        self, payload: BillingProfileTenantAccessCSPPayload
    ):
        sp_token = self._get_sp_token(payload.creds)
        request_body = {
            "properties": {
                "principalTenantId": payload.tenant_id,  # from tenant creation
                "principalId": payload.user_object_id,  # from tenant creationn
                "roleDefinitionId": f"/providers/Microsoft.Billing/billingAccounts/{payload.billing_account_name}/billingProfiles/{payload.billing_profile_name}/billingRoleDefinitions/40000000-aaaa-bbbb-cccc-100000000000",
            }
        }

        headers = {
            "Authorization": f"Bearer {sp_token}",
        }

        url = f"https://management.azure.com/providers/Microsoft.Billing/billingAccounts/{payload.billing_account_name}/billingProfiles/{payload.billing_profile_name}/createBillingRoleAssignment?api-version=2019-10-01-preview"

        result = self.sdk.requests.post(url, headers=headers, json=request_body)
        if result.status_code == 201:
            return self._ok(BillingProfileTenantAccessCSPResult(**result.json()))
        else:
            return self._error(result.json())

    def create_task_order_billing_creation(
        self, payload: TaskOrderBillingCreationCSPPayload
    ):
        sp_token = self._get_sp_token(payload.creds)
        request_body = [
            {
                "op": "replace",
                "path": "/enabledAzurePlans",
                "value": [{"skuId": "0001"}],
            }
        ]

        request_headers = {
            "Authorization": f"Bearer {sp_token}",
        }

        url = f"https://management.azure.com/providers/Microsoft.Billing/billingAccounts/{payload.billing_account_name}/billingProfiles/{payload.billing_profile_name}?api-version=2019-10-01-preview"

        result = self.sdk.requests.patch(
            url, headers=request_headers, json=request_body
        )

        if result.status_code == 202:
            # 202 has location/retry after headers
            return self._ok(TaskOrderBillingCreationCSPResult(**result.headers))
        elif result.status_code == 200:
            return self._ok(TaskOrderBillingVerificationCSPResult(**result.json()))
        else:
            return self._error(result.json())

    def create_task_order_billing_verification(
        self, payload: TaskOrderBillingVerificationCSPPayload
    ):
        sp_token = self._get_sp_token(payload.creds)
        if sp_token is None:
            raise AuthenticationException(
                "Could not resolve token for task order billing validation"
            )

        auth_header = {
            "Authorization": f"Bearer {sp_token}",
        }

        result = self.sdk.requests.get(
            payload.task_order_billing_verify_url, headers=auth_header
        )

        if result.status_code == 202:
            # 202 has location/retry after headers
            return self._ok(TaskOrderBillingCreationCSPResult(**result.headers))
        elif result.status_code == 200:
            return self._ok(TaskOrderBillingVerificationCSPResult(**result.json()))
        else:
            return self._error(result.json())

    def create_billing_instruction(self, payload: BillingInstructionCSPPayload):
        sp_token = self._get_sp_token(payload.creds)
        if sp_token is None:
            raise AuthenticationException(
                "Could not resolve token for task order billing validation"
            )

        request_body = {
            "properties": {
                "amount": payload.initial_clin_amount,
                "startDate": payload.initial_clin_start_date,
                "endDate": payload.initial_clin_end_date,
            }
        }

        url = f"https://management.azure.com/providers/Microsoft.Billing/billingAccounts/{payload.billing_account_name}/billingProfiles/{payload.billing_profile_name}/instructions/{payload.initial_task_order_id}:CLIN00{payload.initial_clin_type}?api-version=2019-10-01-preview"

        auth_header = {
            "Authorization": f"Bearer {sp_token}",
        }

        result = self.sdk.requests.put(url, headers=auth_header, json=request_body)

        if result.status_code == 200:
            return self._ok(BillingInstructionCSPResult(**result.json()))
        else:
            return self._error(result.json())

    def create_product_purchase(
        self, payload: ProductPurchaseCSPPayload
    ):
        sp_token = self._get_sp_token(payload.creds)
        if sp_token is None:
            raise AuthenticationException(
                "Could not resolve token for aad premium product purchase"
            )

        create_product_purchase_body = payload.dict(by_alias=True)
        create_product_purchase_headers = {
            "Authorization": f"Bearer {sp_token}",
        }

        product_purchase_url = f"https://management.azure.com//providers/Microsoft.Billing/billingAccounts/{payload.billing_account_name}/billingProfiles/{payload.billing_profile_name}/products?api-version=2019-10-01-preview"

        result = self.sdk.requests.post(
            product_purchase_url,
            json=create_product_purchase_body,
            headers=create_product_purchase_headers,
        )

        if result.status_code == 202:
            # 202 has location/retry after headers
            return self._ok(ProductPurchaseCSPResult(**result.headers))
        elif result.status_code == 200:
            # NB: Swagger docs imply call can sometimes resolve immediately
            return self._ok(ProductPurchaseCSPResult(**result.json()))
        else:
            return self._error(result.json())


    def create_product_purchase_verification(
        self, payload: ProductPurchaseVerificationCSPPayload
    ):
        sp_token = self._get_sp_token(payload.creds)
        if sp_token is None:
            raise AuthenticationException(
                "Could not resolve token for task order billing validation"
            )

        auth_header = {
            "Authorization": f"Bearer {sp_token}",
        }

        result = self.sdk.requests.get(
            payload.product_purchase_verify_url, headers=auth_header
        )

        if result.status_code == 202:
            # 202 has location/retry after headers
            return self._ok(ProductPurchaseCSPResult(**result.headers))
        elif result.status_code == 200:
            return self._ok(ProductPurchaseVerificationCSPResult(**result.json()))
        else:
            return self._error(result.json())


    def create_remote_admin(self, creds, tenant_details):
        # create app/service principal within tenant, with name constructed from tenant details
        # assign principal global admin

        # needs to call out to CLI with tenant owner username/password, prototyping for that underway

        # return identifier and creds to consumer for storage
        response = {"clientId": "string", "secretKey": "string", "tenantId": "string"}
        return self._ok(
            {
                "client_id": response["clientId"],
                "secret_key": response["secret_key"],
                "tenant_id": response["tenantId"],
            }
        )

    def force_tenant_admin_pw_update(self, creds, tenant_owner_id):
        # use creds to update to force password recovery?
        # not sure what the endpoint/method for this is, yet

        return self._ok()

    def create_billing_alerts(self, TBD):
        # TODO: Add azure-mgmt-consumption for Budget and Notification entities/operations
        # TODO: Determine how to auth against that API using the SDK, doesn't seeem possible at the moment
        # TODO: billing alerts are registered as Notifications on Budget objects, which have start/end dates
        # TODO: determine what the keys in the Notifications dict are supposed to be
        # we may need to rotate budget objects when new TOs/CLINs are reported?

        # we likely only want the budget ID, can be updated or replaced?
        response = {"id": "id"}
        return self._ok({"budget_id": response["id"]})

    def _get_management_service_principal(self):
        # we really should be using graph.microsoft.com, but i'm getting
        # "expired token" errors for that
        # graph_resource = "https://graph.microsoft.com"
        graph_resource = "https://graph.windows.net"
        graph_creds = self._get_credential_obj(
            self._root_creds, resource=graph_resource
        )
        # I needed to set permissions for the graph.windows.net API before I
        # could get this to work.

        # how do we scope the graph client to the new subscription rather than
        # the cloud0 subscription? tenant id seems to be separate from subscription id
        graph_client = self.sdk.graphrbac.GraphRbacManagementClient(
            graph_creds, self._root_creds.get("tenant_id")
        )

        # do we need to create a new application to manage each subscripition
        # or should we manage access to each subscription from a single service
        # principal with multiple role assignments?
        app_display_name = "?"  # name should reflect the subscription it exists
        app_create_param = self.sdk.graphrbac.models.ApplicationCreateParameters(
            display_name=app_display_name
        )

        # we need the appropriate perms here:
        # https://docs.microsoft.com/en-us/graph/api/application-post-applications?view=graph-rest-beta&tabs=http
        # https://docs.microsoft.com/en-us/graph/permissions-reference#microsoft-graph-permission-names
        # set app perms in app registration portal
        # https://docs.microsoft.com/en-us/graph/auth-v2-service#2-configure-permissions-for-microsoft-graph
        app: self.sdk.graphrbac.models.Application = graph_client.applications.create(
            app_create_param
        )

        # create a new service principle for the new application, which should be scoped
        # to the new subscription
        app_id = app.app_id
        sp_create_params = self.sdk.graphrbac.models.ServicePrincipalCreateParameters(
            app_id=app_id, account_enabled=True
        )

        service_principal = graph_client.service_principals.create(sp_create_params)

        return service_principal

    def _extract_subscription_id(self, subscription_url):
        sub_id_match = SUBSCRIPTION_ID_REGEX.match(subscription_url)

        if sub_id_match:
            return sub_id_match.group(1)

    def _get_sp_token(self, creds):
        home_tenant_id = creds.get("home_tenant_id")
        client_id = creds.get("client_id")
        secret_key = creds.get("secret_key")

        # TODO: Make endpoints consts or configs
        authentication_endpoint = "https://login.microsoftonline.com/"
        resource = "https://management.azure.com/"

        context = self.sdk.adal.AuthenticationContext(
            authentication_endpoint + home_tenant_id
        )

        # TODO: handle failure states here
        token_response = context.acquire_token_with_client_credentials(
            resource, client_id, secret_key
        )

        return token_response.get("accessToken", None)

    def _get_credential_obj(self, creds, resource=None):
        return self.sdk.credentials.ServicePrincipalCredentials(
            client_id=creds.get("client_id"),
            secret=creds.get("secret_key"),
            tenant=creds.get("tenant_id"),
            resource=resource,
            cloud_environment=self.sdk.cloud,
        )

    def _get_client_secret_credential_obj(self, creds):
        return self.sdk.identity.ClientSecretCredential(
            tenant_id=creds.get("tenant_id"),
            client_id=creds.get("client_id"),
            client_secret=creds.get("secret_key"),
        )

    def _make_tenant_admin_cred_obj(self, username, password):
        return self.sdk.credentials.UserPassCredentials(username, password)

    def _ok(self, body=None):
        return self._make_response("ok", body)

    def _error(self, body=None):
        return self._make_response("error", body)

    def _make_response(self, status, body=dict()):
        """Create body for responses from API

        Arguments:
            status {string} -- "ok" or "error"
            body {dict} -- dict containing details of response or error, if applicable

        Returns:
            dict -- status of call with body containing details
        """
        return {"status": status, "body": body}

    @property
    def _root_creds(self):
        return {
            "client_id": self.client_id,
            "secret_key": self.secret_key,
            "tenant_id": self.tenant_id,
        }

    def get_credentials(self, scope="portfolio", tenant_id=None):
        """
        This could be implemented to determine, based on type, whether to return creds for:
            - scope="atat": the ATAT main app registration in ATAT's home tenant
            - scope="tenantadmin": the tenant administrator credentials
            - scope="portfolio": the credentials for the ATAT SP in the portfolio tenant
        """
        if scope == "atat":
            return self._root_creds
        elif scope == "tenantadmin":
            # magic with key vault happens
            return {
                "client_id": "some id",
                "secret_key": "very secret",
                "tenant_id": tenant_id,
            }
        elif scope == "portfolio":
            # magic with key vault happens
            return {
                "client_id": "some id",
                "secret_key": "very secret",
                "tenant_id": tenant_id,
            }

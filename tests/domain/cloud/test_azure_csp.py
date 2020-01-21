import pytest
import time
from unittest.mock import Mock
import os

from uuid import uuid4

creds = {
    "home_tenant_id": os.getenv("AZURE_HOME_TENANT_ID"),
    "client_id": os.getenv("AZURE_CLIENT_ID"),
    "secret_key": os.getenv("AZURE_SECRET_KEY"),
}

BILLING_ACCOUNT_NAME = os.getenv("AZURE_BILLING_ACCOUNT")


from atst.domain.csp.cloud import (
    AzureCloudProvider,
    TenantCSPResult,
    TenantCSPPayload,
    BillingProfileCSPPayload,
    BillingProfileAddress,
    BillingProfileCreateCSPResult,
    BillingProfileVerifyCSPPayload,
    BillingProfileCSPResult,
    BillingRoleAssignmentCSPPayload,
    BillingRoleAssignmentCSPResult,
    EnableTaskOrderBillingCSPPayload,
    VerifyTaskOrderBillingCSPPayload,
    BillingProfileEnabledCSPResult,
    ReportCLINCSPPayload,
    ReportCLINCSPResult,
    EnableTaskOrderBillingCSPResult,
)

from tests.mock_azure import mock_azure, AUTH_CREDENTIALS
from tests.factories import EnvironmentFactory, ApplicationFactory


# TODO: Directly test create subscription, provide all args √
# TODO: Test create environment (create management group with parent)
# TODO: Test create application (create manageemnt group with parent)
# Create reusable mock for mocking the management group calls for multiple services
#


@pytest.mark.skip("Skipping legacy azure integration tests")
def test_create_subscription_succeeds(mock_azure: AzureCloudProvider):
    environment = EnvironmentFactory.create()

    subscription_id = str(uuid4())

    credentials = mock_azure._get_credential_obj(AUTH_CREDENTIALS)
    display_name = "Test Subscription"
    billing_profile_id = str(uuid4())
    sku_id = str(uuid4())
    management_group_id = (
        environment.cloud_id  # environment.csp_details.management_group_id?
    )
    billing_account_name = (
        "?"  # environment.application.portfilio.csp_details.billing_account.name?
    )
    invoice_section_name = "?"  # environment.name? or something specific to billing?

    mock_azure.sdk.subscription.SubscriptionClient.return_value.subscription_factory.create_subscription.return_value.result.return_value.subscription_link = (
        f"subscriptions/{subscription_id}"
    )

    result = mock_azure._create_subscription(
        credentials,
        display_name,
        billing_profile_id,
        sku_id,
        management_group_id,
        billing_account_name,
        invoice_section_name,
    )

    assert result == subscription_id


def mock_management_group_create(mock_azure, spec_dict):
    mock_azure.sdk.managementgroups.ManagementGroupsAPI.return_value.management_groups.create_or_update.return_value.result.return_value = Mock(
        **spec_dict
    )


@pytest.mark.skip("Skipping legacy azure integration tests")
def test_create_environment_succeeds(mock_azure: AzureCloudProvider):
    environment = EnvironmentFactory.create()

    mock_management_group_create(mock_azure, {"id": "Test Id"})

    result = mock_azure.create_environment(
        AUTH_CREDENTIALS, environment.creator, environment
    )

    assert result.id == "Test Id"


@pytest.mark.skip("Skipping legacy azure integration tests")
def test_create_application_succeeds(mock_azure: AzureCloudProvider):
    application = ApplicationFactory.create()

    mock_management_group_create(mock_azure, {"id": "Test Id"})

    result = mock_azure._create_application(AUTH_CREDENTIALS, application)

    assert result.id == "Test Id"


@pytest.mark.skip("Skipping legacy azure integration tests")
def test_create_atat_admin_user_succeeds(mock_azure: AzureCloudProvider):
    environment_id = str(uuid4())

    csp_user_id = str(uuid4)

    mock_azure.sdk.graphrbac.GraphRbacManagementClient.return_value.service_principals.create.return_value.object_id = (
        csp_user_id
    )

    result = mock_azure.create_atat_admin_user(AUTH_CREDENTIALS, environment_id)

    assert result.get("csp_user_id") == csp_user_id


@pytest.mark.skip("Skipping legacy azure integration tests")
def test_create_policy_definition_succeeds(mock_azure: AzureCloudProvider):
    subscription_id = str(uuid4())
    management_group_id = str(uuid4())
    properties = {
        "policyType": "test",
        "displayName": "test policy",
    }

    result = mock_azure._create_policy_definition(
        AUTH_CREDENTIALS, subscription_id, management_group_id, properties
    )
    azure_sdk_method = (
        mock_azure.sdk.policy.PolicyClient.return_value.policy_definitions.create_or_update_at_management_group
    )
    mock_policy_definition = (
        mock_azure.sdk.policy.PolicyClient.return_value.policy_definitions.models.PolicyDefinition()
    )
    assert azure_sdk_method.called
    azure_sdk_method.assert_called_with(
        management_group_id=management_group_id,
        policy_definition_name=properties.get("displayName"),
        parameters=mock_policy_definition,
    )


def test_get_billing_accounts(mock_azure: AzureCloudProvider):
    result = mock_azure.get_billing_accounts(creds)
    print(result.json())
    print(result)


def test_create_tenant(mock_azure: AzureCloudProvider):
    # mock_azure.sdk.adal.AuthenticationContext.return_value.context.acquire_token_with_client_credentials.return_value = {
    #     "accessToken": "TOKEN"
    # }

    # mock_result = Mock()
    # mock_result.json.return_value = {
    #     "objectId": "0a5f4926-e3ee-4f47-a6e3-8b0a30a40e3d",
    #     "tenantId": "60ff9d34-82bf-4f21-b565-308ef0533435",
    #     "userId": "1153801116406515559",
    # }
    # mock_result.status_code = 200
    # mock_azure.sdk.requests.post.return_value = mock_result
    payload = TenantCSPPayload(
        **dict(
            creds=creds,
            user_id="admin",
            password="JediJan13$coot",
            domain_name="sccadisa",
            first_name="Scott",
            last_name="Peeples",
            country_code="US",
            password_recovery_email_address="peeps@friends.dds.mil",
        )
    )
    result = mock_azure.create_tenant(payload)
    body: TenantCSPResult = result.get("body")
    assert body.tenant_id == "60ff9d34-82bf-4f21-b565-308ef0533435"


def test_create_billing_profile(mock_azure: AzureCloudProvider):
    # mock_azure.sdk.adal.AuthenticationContext.return_value.context.acquire_token_with_client_credentials.return_value = {
    #     "accessToken": "TOKEN"
    # }

    # mock_result = Mock()
    # mock_result.headers = {
    #     "Location": "http://retry-url",
    #     "Retry-After": "10",
    # }
    # mock_result.status_code = 202
    # mock_azure.sdk.requests.post.return_value = mock_result
    payload = BillingProfileCSPPayload(
        **dict(
            address=dict(
                address_line_1="6000 DEFENSE PENTAGON SUITE 5E564",
                company_name="CCPO",
                city="Washington",
                region="DC",
                country="US",
                postal_code="20301-6000",
            ),
            creds=creds,
            tenant_id="5e1f98af-50f3-493f-8081-1841bbde715e",
            billing_profile_display_name="ATAT Billing Profile",
            billing_account_name=BILLING_ACCOUNT_NAME,
        )
    )
    result = mock_azure.create_billing_profile(payload)
    body: BillingProfileCreateCSPResult = result.get("body")
    print(body.billing_profile_validate_url)
    assert body.retry_after == 10


def test_validate_billing_profile_creation(mock_azure: AzureCloudProvider):
    # mock_azure.sdk.adal.AuthenticationContext.return_value.context.acquire_token_with_client_credentials.return_value = {
    #     "accessToken": "TOKEN"
    # }

    # mock_result = Mock()
    # mock_result.status_code = 200
    # mock_result.json.return_value = {
    #     "id": "/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/billingProfiles/KQWI-W2SU-BG7-TGB",
    #     "name": "KQWI-W2SU-BG7-TGB",
    #     "properties": {
    #         "address": {
    #             "addressLine1": "123 S Broad Street, Suite 2400",
    #             "city": "Philadelphia",
    #             "companyName": "Promptworks",
    #             "country": "US",
    #             "postalCode": "19109",
    #             "region": "PA",
    #         },
    #         "currency": "USD",
    #         "displayName": "First Portfolio Billing Profile",
    #         "enabledAzurePlans": [],
    #         "hasReadAccess": True,
    #         "invoiceDay": 5,
    #         "invoiceEmailOptIn": False,
    #         "invoiceSections": [
    #             {
    #                 "id": "/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/billingProfiles/KQWI-W2SU-BG7-TGB/invoiceSections/6HMZ-2HLO-PJA-TGB",
    #                 "name": "6HMZ-2HLO-PJA-TGB",
    #                 "properties": {"displayName": "First Portfolio Billing Profile"},
    #                 "type": "Microsoft.Billing/billingAccounts/billingProfiles/invoiceSections",
    #             }
    #         ],
    #     },
    #     "type": "Microsoft.Billing/billingAccounts/billingProfiles",
    # }
    # mock_azure.sdk.requests.get.return_value = mock_result

    payload = BillingProfileVerifyCSPPayload(
        **dict(
            creds=creds,
            billing_profile_validate_url="https://management.azure.com/providers/Microsoft.Billing/billingAccounts/60623a61-9283-5594-00e6-f1d4124a07c6:3ad5fb00-5637-45bd-8aaa-2157d1b6722c_2019-05-31/operationResults/createBillingProfile_2a6dbfb6-4e55-44a4-b80a-4e3aee4c0fbd?api-version=2019-10-01-preview",
        )
    )

    result = mock_azure.validate_billing_profile_created(payload)
    body: BillingProfileCSPResult = result.get("body")
    print(body)
    assert body.billing_profile_name == "KQWI-W2SU-BG7-TGB"
    assert (
        body.billing_profile_properties.billing_profile_display_name
        == "First Portfolio Billing Profile"
    )


def test_grant_billing_profile_tenant_access(mock_azure: AzureCloudProvider):
    # mock_azure.sdk.adal.AuthenticationContext.return_value.context.acquire_token_with_client_credentials.return_value = {
    #     "accessToken": "TOKEN"
    # }

    # mock_result = Mock()
    # mock_result.status_code = 201
    # mock_result.json.return_value = {
    #     "id": "/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/billingProfiles/KQWI-W2SU-BG7-TGB/billingRoleAssignments/40000000-aaaa-bbbb-cccc-100000000000_0a5f4926-e3ee-4f47-a6e3-8b0a30a40e3d",
    #     "name": "40000000-aaaa-bbbb-cccc-100000000000_0a5f4926-e3ee-4f47-a6e3-8b0a30a40e3d",
    #     "properties": {
    #         "createdOn": "2020-01-14T14:39:26.3342192+00:00",
    #         "createdByPrincipalId": "82e2b376-3297-4096-8743-ed65b3be0b03",
    #         "principalId": "0a5f4926-e3ee-4f47-a6e3-8b0a30a40e3d",
    #         "principalTenantId": "60ff9d34-82bf-4f21-b565-308ef0533435",
    #         "roleDefinitionId": "/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/billingProfiles/KQWI-W2SU-BG7-TGB/billingRoleDefinitions/40000000-aaaa-bbbb-cccc-100000000000",
    #         "scope": "/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/billingProfiles/KQWI-W2SU-BG7-TGB",
    #     },
    #     "type": "Microsoft.Billing/billingRoleAssignments",
    # }

    # mock_azure.sdk.requests.post.return_value = mock_result
    # ben admin object id: "6e945ba6-d864-45ac-9793-a2ce410c1a06"
    # scott admin object id: "e7960de3-c441-4ec1-a17b-5ff216fde208"

    payload = BillingRoleAssignmentCSPPayload(
        **dict(
            creds=creds,
            tenant_id="5e1f98af-50f3-493f-8081-1841bbde715e",
            user_object_id="85f111f6-4a02-43bd-b6dc-b55906258cf1",
            billing_account_name=BILLING_ACCOUNT_NAME,
            billing_profile_name="FPJJ-DINF-BG7-PGB",
        )
    )

    result = mock_azure.grant_billing_profile_tenant_access(payload)
    body: BillingRoleAssignmentCSPResult = result.get("body")
    print(body)
    assert (
        body.billing_role_assignment_name
        == "40000000-aaaa-bbbb-cccc-100000000000_0a5f4926-e3ee-4f47-a6e3-8b0a30a40e3d"
    )


def test_enable_task_order_billing(mock_azure: AzureCloudProvider):
    # mock_azure.sdk.adal.AuthenticationContext.return_value.context.acquire_token_with_client_credentials.return_value = {
    #     "accessToken": "TOKEN"
    # }

    # mock_result = Mock()
    # mock_result.status_code = 202
    # mock_result.headers = {
    #     "Location": "https://management.azure.com/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/operationResults/patchBillingProfile_KQWI-W2SU-BG7-TGB:02715576-4118-466c-bca7-b1cd3169ff46?api-version=2019-10-01-preview",
    #     "Retry-After": "10",
    # }

    # mock_azure.sdk.requests.patch.return_value = mock_result

    payload = EnableTaskOrderBillingCSPPayload(
        **dict(
            creds=creds,
            billing_account_name=BILLING_ACCOUNT_NAME,
            billing_profile_name="FPJJ-DINF-BG7-PGB",
        )
    )

    result = mock_azure.enable_task_order_billing(payload)
    body: BillingProfileCreateCSPResult = result.get("body")
    print(body.billing_profile_validate_url)
    assert (
        body.billing_profile_validate_url
        == "https://management.azure.com/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/operationResults/patchBillingProfile_KQWI-W2SU-BG7-TGB:02715576-4118-466c-bca7-b1cd3169ff46?api-version=2019-10-01-preview"
    )


def test_validate_task_order_billing_enabled(mock_azure: AzureCloudProvider):
    # mock_azure.sdk.adal.AuthenticationContext.return_value.context.acquire_token_with_client_credentials.return_value = {
    #     "accessToken": "TOKEN"
    # }

    # mock_result = Mock()
    # mock_result.status_code = 200
    # mock_result.json.return_value = {
    #     "id": "/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/billingProfiles/KQWI-W2SU-BG7-TGB",
    #     "name": "KQWI-W2SU-BG7-TGB",
    #     "properties": {
    #         "address": {
    #             "addressLine1": "123 S Broad Street, Suite 2400",
    #             "city": "Philadelphia",
    #             "companyName": "Promptworks",
    #             "country": "US",
    #             "postalCode": "19109",
    #             "region": "PA",
    #         },
    #         "currency": "USD",
    #         "displayName": "Test Billing Profile",
    #         "enabledAzurePlans": [
    #             {
    #                 "productId": "DZH318Z0BPS6",
    #                 "skuId": "0001",
    #                 "skuDescription": "Microsoft Azure Plan",
    #             }
    #         ],
    #         "hasReadAccess": True,
    #         "invoiceDay": 5,
    #         "invoiceEmailOptIn": False,
    #         "invoiceSections": [
    #             {
    #                 "id": "/providers/Microsoft.Billing/billingAccounts/7c89b735-b22b-55c0-ab5a-c624843e8bf6:de4416ce-acc6-44b1-8122-c87c4e903c91_2019-05-31/billingProfiles/KQWI-W2SU-BG7-TGB/invoiceSections/CHCO-BAAR-PJA-TGB",
    #                 "name": "CHCO-BAAR-PJA-TGB",
    #                 "properties": {"displayName": "Test Billing Profile"},
    #                 "type": "Microsoft.Billing/billingAccounts/billingProfiles/invoiceSections",
    #             }
    #         ],
    #     },
    #     "type": "Microsoft.Billing/billingAccounts/billingProfiles",
    # }
    # mock_azure.sdk.requests.get.return_value = mock_result

    payload = VerifyTaskOrderBillingCSPPayload(
        **dict(
            creds=creds,
            task_order_billing_validation_url="https://management.azure.com/providers/Microsoft.Billing/billingAccounts/60623a61-9283-5594-00e6-f1d4124a07c6:3ad5fb00-5637-45bd-8aaa-2157d1b6722c_2019-05-31/operationResults/patchBillingProfile_FHEH-ENLC-BG7-PGB:c5400cba-4878-44d1-9974-bab4ac7fe50d?api-version=2019-10-01-preview",
        )
    )

    result = mock_azure.validate_task_order_billing_enabled(payload)
    body: BillingProfileEnabledCSPResult = result.get("body")
    print(body)
    assert body.billing_profile_name == "KQWI-W2SU-BG7-TGB"
    assert (
        body.billing_profile_enabled_plan_details.enabled_azure_plans[0].get("skuId")
        == "0001"
    )


def test_report_clin(mock_azure: AzureCloudProvider):
    # mock_azure.sdk.adal.AuthenticationContext.return_value.context.acquire_token_with_client_credentials.return_value = {
    #     "accessToken": "TOKEN"
    # }

    # mock_result = Mock()
    # mock_result.status_code = 200
    # mock_result.json.return_value = {
    #     "name": "TO1:CLIN001",
    #     "properties": {
    #         "amount": 1000.0,
    #         "endDate": "2020-03-01T00:00:00+00:00",
    #         "startDate": "2020-01-01T00:00:00+00:00",
    #     },
    #     "type": "Microsoft.Billing/billingAccounts/billingProfiles/billingInstructions",
    # }

    # mock_azure.sdk.requests.put.return_value = mock_result

    payload = ReportCLINCSPPayload(
        **dict(
            creds=creds,
            amount=563513.57,
            start_date="2020/1/6",
            end_date="2021/1/5",
            clin_type="1",
            task_order_id="HQ003420F0056",
            billing_account_name=BILLING_ACCOUNT_NAME,
            billing_profile_name="FHEH-ENLC-BG7-PGB",
        )
    )
    result = mock_azure.report_clin(payload)
    body: ReportCLINCSPResult = result.get("body")
    print(body)
    assert body.reported_clin_name == "TO1:CLIN001"


def test_azure_production(mock_azure: AzureCloudProvider):
    """This function will run through the complete process of standing up a new tenant and authorizing it for billing.
    Before running this, you will need to do a few things.

    1. See the top of this file for what environment variables need to be present to populate credentials and other config values
    2. Go to mock_azure.py and return the real, non-mock versions of both adal and requests from the appropriate functions
        * mock_adal
        * mock_requests
    3. Populate these data payloads below with the appropriate values:
        * TenantCSPPayload
        * BillingProfileCSPPayload
        * ReportCLINCSPPayload
    4. Run just this test with:
        * pipenv run python -m pytest --no-cov -s tests/domain/cloud/test_azure_csp.py -k "test_azure_production"
    5. You should see output per step as it stands up the environment. Note: Unfortunately this script expects the happy
        path at the moment, so if something goes wrong, you'll have to revert to doing it step by step with the individual
        tests above, pasting in appropriate values from the printouts and commenting out the mock sections.
    """
    ct_payload = TenantCSPPayload(
        **dict(
            creds=creds,
            user_id="admin",
            password="JediJan13$coot",
            domain_name="jediccpotestintegration",
            first_name="Tom",
            last_name="Chandler",
            country_code="US",
            password_recovery_email_address="thomas@promptworks.com",
        )
    )
    ct_result = mock_azure.create_tenant(ct_payload)
    tc_body: TenantCSPResult = ct_result.get("body")
    print("tenant created!")
    print(tc_body)

    billing_profile_create_payload = BillingProfileCSPPayload(
        **dict(
            address=dict(
                address_line_1="6000 DEFENSE PENTAGON SUITE 5E564",
                company_name="CCPO",
                city="Washington",
                region="DC",
                country="US",
                postal_code="20301-6000",
            ),
            creds=creds,
            tenant_id=tc_body.tenant_id,
            billing_profile_display_name="ATAT Billing Profile",
            billing_account_name=BILLING_ACCOUNT_NAME,
        )
    )
    cb_result = mock_azure.create_billing_profile(billing_profile_create_payload)
    cb_body: BillingProfileCreateCSPResult = cb_result.get("body")
    print("billing profile creation requested!")
    print(cb_body)

    # sleep for:
    time.sleep(cb_body.retry_after * 2)

    vbp_payload = BillingProfileVerifyCSPPayload(
        **dict(
            creds=creds,
            billing_profile_validate_url=cb_body.billing_profile_validate_url,
        )
    )

    vbp_result = mock_azure.validate_billing_profile_created(vbp_payload)
    vbp_body: BillingProfileCSPResult = vbp_result.get("body")
    print("billing profile creation verified!")
    print(vbp_body)

    bra_payload = BillingRoleAssignmentCSPPayload(
        **dict(
            creds=creds,
            tenant_id=tc_body.tenant_id,
            user_object_id=tc_body.user_object_id,
            billing_account_name=BILLING_ACCOUNT_NAME,
            billing_profile_name=vbp_body.billing_profile_name,
        )
    )

    bra_result = mock_azure.grant_billing_profile_tenant_access(bra_payload)
    bra_body: BillingRoleAssignmentCSPResult = bra_result.get("body")
    print("billing profile role assignment... assigned!")
    print(bra_body)

    etb_payload = EnableTaskOrderBillingCSPPayload(
        **dict(
            creds=creds,
            billing_account_name=BILLING_ACCOUNT_NAME,
            billing_profile_name=vbp_body.billing_profile_name,
        )
    )

    etb_result = mock_azure.enable_task_order_billing(etb_payload)
    etb_body: BillingProfileCreateCSPResult = etb_result.get("body")
    print("task order billing requested")
    print(etb_body)

    time.sleep(etb_body.retry_after * 2)

    vtob_payload = VerifyTaskOrderBillingCSPPayload(
        **dict(
            creds=creds,
            task_order_billing_validation_url=etb_body.billing_profile_validate_url,
        )
    )

    vtob_result = mock_azure.validate_task_order_billing_enabled(vtob_payload)
    vtob_body: BillingProfileEnabledCSPResult = vtob_result.get("body")
    print("task order billing verified")
    print(vtob_body)

    rc_payload = ReportCLINCSPPayload(
        **dict(
            creds=creds,
            amount=1000.00,
            start_date="2020/1/6",
            end_date="2021/1/5",
            clin_type="1",
            task_order_id="FAKE",
            billing_account_name=BILLING_ACCOUNT_NAME,
            billing_profile_name=vtob_body.billing_profile_name,
        )
    )
    rc_result = mock_azure.report_clin(rc_payload)
    rc_body: ReportCLINCSPResult = rc_result.get("body")
    print("clin reported!")
    print(rc_body)

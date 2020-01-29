from typing import Dict, List, Optional
import re
from uuid import uuid4

from pydantic import BaseModel, validator, root_validator

from atst.utils import snake_to_camel


class AliasModel(BaseModel):
    """
    This provides automatic camel <-> snake conversion for serializing to/from json
    You can override the alias generation in subclasses by providing a Config that defines
    a fields property with a dict mapping variables to their cast names, for cases like:
    * some_url:someURL
    * user_object_id:objectId
    """

    class Config:
        alias_generator = snake_to_camel
        allow_population_by_field_name = True


class BaseCSPPayload(AliasModel):
    # {"username": "mock-cloud", "pass": "shh"}
    creds: Dict

    def dict(self, *args, **kwargs):
        exclude = {"creds"}
        if "exclude" not in kwargs:
            kwargs["exclude"] = exclude
        else:
            kwargs["exclude"].update(exclude)

        return super().dict(*args, **kwargs)


class TenantCSPPayload(BaseCSPPayload):
    user_id: str
    password: Optional[str]
    domain_name: str
    first_name: str
    last_name: str
    country_code: str
    password_recovery_email_address: str


class TenantCSPResult(AliasModel):
    user_id: str
    tenant_id: str
    user_object_id: str

    tenant_admin_username: Optional[str]
    tenant_admin_password: Optional[str]

    class Config:
        fields = {
            "user_object_id": "objectId",
        }

    def dict(self, *args, **kwargs):
        exclude = {"tenant_admin_username", "tenant_admin_password"}
        if "exclude" not in kwargs:
            kwargs["exclude"] = exclude
        else:
            kwargs["exclude"].update(exclude)

        return super().dict(*args, **kwargs)

    def get_creds(self):
        return {
            "tenant_admin_username": self.tenant_admin_username,
            "tenant_admin_password": self.tenant_admin_password,
            "tenant_id": self.tenant_id,
        }


class BillingProfileAddress(AliasModel):
    company_name: str
    address_line_1: str
    city: str
    region: str
    country: str
    postal_code: str


class BillingProfileCLINBudget(AliasModel):
    clin_budget: Dict
    """
        "clinBudget": {
            "amount": 0,
            "startDate": "2019-12-18T16:47:40.909Z",
            "endDate": "2019-12-18T16:47:40.909Z",
            "externalReferenceId": "string"
        }
    """


class BillingProfileCreationCSPPayload(BaseCSPPayload):
    tenant_id: str
    billing_profile_display_name: str
    billing_account_name: str
    enabled_azure_plans: Optional[List[str]]
    address: BillingProfileAddress

    @validator("enabled_azure_plans", pre=True, always=True)
    def default_enabled_azure_plans(cls, v):
        """
        Normally you'd implement this by setting the field with a value of:
            dataclasses.field(default_factory=list)
        but that prevents the object from being correctly pickled, so instead we need
        to rely on a validator to ensure this has an empty value when not specified
        """
        return v or []

    class Config:
        fields = {"billing_profile_display_name": "displayName"}


class BillingProfileCreationCSPResult(AliasModel):
    billing_profile_verify_url: str
    billing_profile_retry_after: int

    class Config:
        fields = {
            "billing_profile_verify_url": "Location",
            "billing_profile_retry_after": "Retry-After",
        }


class BillingProfileVerificationCSPPayload(BaseCSPPayload):
    billing_profile_verify_url: str


class BillingInvoiceSection(AliasModel):
    invoice_section_id: str
    invoice_section_name: str

    class Config:
        fields = {"invoice_section_id": "id", "invoice_section_name": "name"}


class BillingProfileProperties(AliasModel):
    address: BillingProfileAddress
    billing_profile_display_name: str
    invoice_sections: List[BillingInvoiceSection]

    class Config:
        fields = {"billing_profile_display_name": "displayName"}


class BillingProfileVerificationCSPResult(AliasModel):
    billing_profile_id: str
    billing_profile_name: str
    billing_profile_properties: BillingProfileProperties

    class Config:
        fields = {
            "billing_profile_id": "id",
            "billing_profile_name": "name",
            "billing_profile_properties": "properties",
        }


class BillingProfileTenantAccessCSPPayload(BaseCSPPayload):
    tenant_id: str
    user_object_id: str
    billing_account_name: str
    billing_profile_name: str


class BillingProfileTenantAccessCSPResult(AliasModel):
    billing_role_assignment_id: str
    billing_role_assignment_name: str

    class Config:
        fields = {
            "billing_role_assignment_id": "id",
            "billing_role_assignment_name": "name",
        }


class TaskOrderBillingCreationCSPPayload(BaseCSPPayload):
    billing_account_name: str
    billing_profile_name: str


class TaskOrderBillingCreationCSPResult(AliasModel):
    task_order_billing_verify_url: str
    task_order_retry_after: int

    class Config:
        fields = {
            "task_order_billing_verify_url": "Location",
            "task_order_retry_after": "Retry-After",
        }


class TaskOrderBillingVerificationCSPPayload(BaseCSPPayload):
    task_order_billing_verify_url: str


class BillingProfileEnabledPlanDetails(AliasModel):
    enabled_azure_plans: List[Dict]


class TaskOrderBillingVerificationCSPResult(AliasModel):
    billing_profile_id: str
    billing_profile_name: str
    billing_profile_enabled_plan_details: BillingProfileEnabledPlanDetails

    class Config:
        fields = {
            "billing_profile_id": "id",
            "billing_profile_name": "name",
            "billing_profile_enabled_plan_details": "properties",
        }


class BillingInstructionCSPPayload(BaseCSPPayload):
    initial_clin_amount: float
    initial_clin_start_date: str
    initial_clin_end_date: str
    initial_clin_type: str
    initial_task_order_id: str
    billing_account_name: str
    billing_profile_name: str


class BillingInstructionCSPResult(AliasModel):
    reported_clin_name: str

    class Config:
        fields = {
            "reported_clin_name": "name",
        }


AZURE_MGMNT_PATH = "/providers/Microsoft.Management/managementGroups/"

MANAGEMENT_GROUP_NAME_REGEX = "^[a-zA-Z0-9\-_\(\)\.]+$"


class ManagementGroupCSPPayload(AliasModel):
    """
    :param: management_group_name: Just pass a UUID for this.
    :param: display_name: This can contain any character and
        spaces, but should be 90 characters or fewer long.
    :param: parent_id: This should be the fully qualified Azure ID,
        i.e. /providers/Microsoft.Management/managementGroups/[management group ID]
    """

    tenant_id: str
    management_group_name: Optional[str]
    display_name: str
    parent_id: str

    @validator("management_group_name", pre=True, always=True)
    def supply_management_group_name_default(cls, name):
        if name:
            if re.match(MANAGEMENT_GROUP_NAME_REGEX, name) is None:
                raise ValueError(
                    f"Management group name must match {MANAGEMENT_GROUP_NAME_REGEX}"
                )

            return name[0:90]
        else:
            return str(uuid4())

    @validator("display_name", pre=True, always=True)
    def enforce_display_name_length(cls, name):
        return name[0:90]

    @validator("parent_id", pre=True, always=True)
    def enforce_parent_id_pattern(cls, id_):
        if AZURE_MGMNT_PATH not in id_:
            return f"{AZURE_MGMNT_PATH}{id_}"
        else:
            return id_


class ManagementGroupCSPResponse(AliasModel):
    id: str


class ApplicationCSPPayload(ManagementGroupCSPPayload):
    pass


class ApplicationCSPResult(ManagementGroupCSPResponse):
    pass


class EnvironmentCSPPayload(ManagementGroupCSPPayload):
    pass


class EnvironmentCSPResult(ManagementGroupCSPResponse):
    pass


class KeyVaultCredentials(BaseModel):
    root_sp_client_id: Optional[str]
    root_sp_key: Optional[str]
    root_tenant_id: Optional[str]

    tenant_id: Optional[str]

    tenant_admin_username: Optional[str]
    tenant_admin_password: Optional[str]

    tenant_sp_client_id: Optional[str]
    tenant_sp_key: Optional[str]

    @root_validator(pre=True)
    def enforce_admin_creds(cls, values):
        tenant_id = values.get("tenant_id")
        username = values.get("tenant_admin_username")
        password = values.get("tenant_admin_password")
        if any([username, password]) and not all([tenant_id, username, password]):
            raise ValueError(
                "tenant_id, tenant_admin_username, and tenant_admin_password must all be set if any one is"
            )

        return values

    @root_validator(pre=True)
    def enforce_sp_creds(cls, values):
        tenant_id = values.get("tenant_id")
        client_id = values.get("tenant_sp_client_id")
        key = values.get("tenant_sp_key")
        if any([client_id, key]) and not all([tenant_id, client_id, key]):
            raise ValueError(
                "tenant_id, tenant_sp_client_id, and tenant_sp_key must all be set if any one is"
            )

        return values

    @root_validator(pre=True)
    def enforce_root_creds(cls, values):
        sp_creds = [
            values.get("root_tenant_id"),
            values.get("root_sp_client_id"),
            values.get("root_sp_key"),
        ]
        if any(sp_creds) and not all(sp_creds):
            raise ValueError(
                "root_tenant_id, root_sp_client_id, and root_sp_key must all be set if any one is"
            )

        return values

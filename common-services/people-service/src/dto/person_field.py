"""Fields of a person request / row (a product's profile plugin may add more)."""
from enum import Enum


class PersonField(str, Enum):
    PERSON_ID = "person_id"
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    PHOTO_ID = "photo_id"
    REF_CODE = "ref_code"
    REFERRED_BY = "referred_by"
    INVITE_CODE = "invite_code"
    CAL_TOKEN = "cal_token"
    SOURCE = "source"
    ALLOW_NO_EMAIL = "allow_no_email"
    TENANT_ID = "tenant_id"
    CREATED = "created"
    LINK = "link"

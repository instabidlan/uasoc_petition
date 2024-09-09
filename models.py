from pydantic import BaseModel, field_validator


class BtnLabelsModel(BaseModel):
    approve: str
    decline: str
    jump: str


class ThreadTagsModel(BaseModel):
    approve_tag: str
    decline_tag: str
    pending_tag: str


class ConfigModel(BaseModel):

    channel_id: int
    info_channel_id: int
    approve_threshold: int
    check_rate: int
    embed_color: int
    approval_emoji: str
    btn_labels: BtnLabelsModel
    tags: ThreadTagsModel
    allowed_emojis: list[str]

    @field_validator("check_rate")
    @classmethod
    def validate_check_rate(cls, value: int) -> int:
        if value < 15:
            raise ValueError("check_rate should be bigger than 15")
        return value

    @field_validator("approve_threshold")
    @classmethod
    def validate_approve_threshold(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("approve_threshold should be bigger than 0")
        return value

    @field_validator("approval_emoji")
    @classmethod
    def validate_approval_emoji(cls, values: list[str]) -> list[str]:
        if len(values) == 0:
            raise ValueError(
                """
                approval_emoji should have at least one element in array
                """
            )
        return values


class ActivePetitionStoreModel(BaseModel):
    thread_id: int
    message_id: int


class StoreModel(BaseModel):
    active_petitions: list[ActivePetitionStoreModel]

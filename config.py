import json
from typing import Sequence

from discord import ForumTag

from models import ConfigModel


DEFAULT_CONFIG_PATH = "./config.json"


class Config:
    CHANNEL_ID: str
    INFO_CHANNEL_ID: str
    ALLOWED_EMOJIS: str
    APPROVE_THRESHOLD: str
    CHECK_RATE: str
    APPROVAL_EMOJI: str
    EMBED_COLOR: str

    APPROVE_BUTTON_LABEL: str
    DECLINE_BUTTON_LABEL: str
    JUMP_BUTTON_LABEL: str

    APPROVE_TAG: str | None = None
    DECLINE_TAG: str | None = None
    PENDING_TAG: str | None = None

    available_tags: list[ForumTag]
    config: ConfigModel

    def __init__(self):
        self.__load_env()
        self.config = self.__load_config()
        self.__configure()

    def __load_config(
        self,
        config_file: str = DEFAULT_CONFIG_PATH
    ) -> ConfigModel:
        with open(config_file, "r") as file:
            parsed_config: ConfigModel.dict = json.load(file)
            file.close()

        return ConfigModel(**parsed_config)

    def __configure(self) -> None:
        self.CHANNEL_ID = self.config.channel_id
        self.INFO_CHANNEL_ID = self.config.info_channel_id
        self.ALLOWED_EMOJIS = self.config.allowed_emojis
        self.APPROVE_THRESHOLD = self.config.approve_threshold
        self.CHECK_RATE = self.config.check_rate
        self.APPROVAL_EMOJI = self.config.approval_emoji
        self.EMBED_COLOR = self.config.embed_color
        self.APPROVE_BUTTON_LABEL = self.config.btn_labels.approve
        self.DECLINE_BUTTON_LABEL = self.config.btn_labels.decline
        self.JUMP_BUTTON_LABEL = self.config.btn_labels.jump

    def set_available_tags(self, forum_tags: Sequence[ForumTag]) -> None:
        self.available_tags = forum_tags
        self.APPROVE_TAG = self.__get_thread_tag(self.config.tags.approve_tag)
        self.DECLINE_TAG = self.__get_thread_tag(self.config.tags.decline_tag)
        self.PENDING_TAG = self.__get_thread_tag(self.config.tags.pending_tag)

    def __get_thread_tag(self, tag_name: str) -> ForumTag:
        filtered_tag = list(
            filter(lambda tag: tag.name == tag_name, self.available_tags)
        )
        if len(filtered_tag) == 0:
            raise ValueError(f"Forum Tag with name {tag_name} not found!")

        return filtered_tag[0]

    def __load_env(self):
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass

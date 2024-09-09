import os
import json

from models import StoreModel, ActivePetitionStoreModel

DEFAULT_STORE_PATH = "./message_store.json"


class StoreManager:

    STORE_FILE: str = ""
    STORE_STATE: StoreModel

    def __init__(self, store_file_path: str | None = None):
        if not store_file_path:
            store_file_path = DEFAULT_STORE_PATH
        self.__is_file_exists(store_file_path=store_file_path)
        self.__load_store()

    def __is_file_exists(self, store_file_path: str | None = None) -> None:
        if not store_file_path:
            store_file_path = self.STORE_FILE
        if not os.path.isfile(store_file_path):
            raise FileExistsError(f"File not exists: {self.STORE_FILE}")
        self.STORE_FILE = store_file_path

    def __read_file(self) -> StoreModel:
        self.__is_file_exists()
        parsed_store_file = None
        with open(self.STORE_FILE, "r") as store_file:
            parsed_store_file = json.load(store_file)
            store_file.close()

        return StoreModel(**parsed_store_file)

    def __load_store(self) -> StoreModel:
        self.STORE_STATE = self.__read_file()
        return self.STORE_STATE

    def __override_file(self, data: StoreModel) -> None:
        self.__is_file_exists()
        with open(self.STORE_FILE, "w") as store_file:
            json.dump(data.model_dump(), store_file, indent=4)
            store_file.close()
        self.__load_store()

    def __save_store_to_file(self) -> None:
        self.__override_file(data=self.STORE_STATE)

    def __add_active_petition_to_store(
        self,
        petition: ActivePetitionStoreModel
    ):
        self.STORE_STATE.active_petitions.append(petition)
        self.__save_store_to_file()

    def get_store(self) -> StoreModel:
        return self.STORE_STATE

    def get_active_petitions_store(self) -> list[ActivePetitionStoreModel]:
        return self.STORE_STATE.active_petitions

    def set_active_petitions_store(
        self,
        data_list: list[ActivePetitionStoreModel]
    ):
        self.__override_file(StoreModel(active_petitions=data_list))

    def add_active_petitions_to_store(
        self, active_petition: ActivePetitionStoreModel
    ) -> None:
        self.__add_active_petition_to_store(active_petition)

    def is_petitio_exists(self, active_petitio_id: int) -> bool:
        filtered_petition = list(
            filter(
                lambda petition: petition.thread_id == active_petitio_id,
                self.get_active_petitions_store(),
            )
        )
        if filtered_petition:
            return True
        return False

    def remove_active_petition(self, active_petition_id: int) -> bool:
        filtered_petitions = list(
            filter(
                lambda petition: petition.thread_id != active_petition_id,
                self.get_active_petitions_store(),
            )
        )
        self.set_active_petitions_store(filtered_petitions)

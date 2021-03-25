from util.db_util import DBUtil
from util.config_options import ConfigOption


class CFUtil:
    def __init__(self, db_util: DBUtil):
        self.db_util = db_util

    @staticmethod
    def __get_cf_option(param: str) -> ConfigOption:
        option: ConfigOption = ConfigOption.NONE
        for name, member in ConfigOption.__members__.items():
            if param.lower() == name:
                option = member
                break
        return option

    def set_param(self, param: str, value):
        option = self.__get_cf_option(param)
        if option == ConfigOption.NONE:
            raise ValueError("Invalid config parameter!")
        if param == ConfigOption.prefix.name:
            try:
                val = ord(value)
            except TypeError:
                raise TypeError("Invalid value for parameter \"prefix\"")
        elif param == ConfigOption.meme_reviewer_role.name or \
                param == ConfigOption.meme_review_channel.name or \
                param == ConfigOption.admin_role.name:
            val = value.id
        else:
            if value.lower() == 'true':
                val = 1
            elif value.lower() == 'false':
                val = 0
            else:
                raise ValueError(f"Invalid value for parameter {param}")
        self.db_util.set_config_option(option, val)

    def get_param(self, param: str):
        option = self.__get_cf_option(param)
        if option == ConfigOption.NONE:
            raise ValueError("Invalid config parameter!")
        result = self.db_util.get_config_option(option)
        return result

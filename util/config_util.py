from util.db_util import DBUtil
from util.config_options import ConfigOption


class CFUtil:
    def __init__(self, db_util: DBUtil):
        self.db_util = db_util

    def set_param(self, param: ConfigOption, value):
        if param not in ConfigOption:
            raise ValueError("Invalid config parameter!")
        if param == ConfigOption.NONE:
            raise ValueError("Invalid config parameter!")
        if param == ConfigOption.prefix:
            try:
                val = ord(value)
            except TypeError:
                raise TypeError("Invalid value for parameter \"prefix\"")
        elif param == ConfigOption.meme_reviewer_role or \
                param == ConfigOption.meme_review_channel or \
                param == ConfigOption.admin_role:
            val = value.id
        else:
            if value.lower() == 'true':
                val = 1
            elif value.lower() == 'false':
                val = 0
            else:
                raise ValueError(f"Invalid value for parameter {param.name}")
        self.db_util.set_config_option(param, val)

    def get_param(self, param: ConfigOption):
        if param not in ConfigOption:
            raise ValueError("Invalid config parameter!")
        if param == ConfigOption.NONE:
            raise ValueError("Invalid config parameter!")
        result = self.db_util.get_config_option(param)
        return result

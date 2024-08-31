import os
from abc import ABC


class EnvVarsTranslater(ABC):
    @staticmethod
    def get_bool(env_var_name: str) -> bool:
        valid_values: list[str] = ["true", "false"]

        env_value: str = os.getenv(env_var_name).lower().strip()

        if env_value not in valid_values:
            raise Exception(
                f"It was not possible convert the env variable {
                    env_var_name} with the value {env_value} to "
                f"'bool'. The value needs to respect the options: {valid_values}")

        return env_value == "true"

    @staticmethod
    def get_int(env_var_name: str) -> int:
        env_value: str = os.getenv(env_var_name).lower().strip()

        try:
            return int(env_value)
        except Exception:
            raise Exception(
                f"It was not possible convert the env variable '{
                    env_var_name}' with the value '{env_value}' to "
                f"'int'. The value needs to be an integer")

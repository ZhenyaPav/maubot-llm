from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper

class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("character_card_path")
        helper.copy("max_tokens")
        helper.copy("enable_multi_user")
        helper.copy("allowed_users")
        helper.copy("max_words")
        helper.copy("max_context_messages")
        helper.copy("reply_in_thread")
        helper.copy("temperature")
        helper.copy("respond_to_replies")
        helper.copy("upload_avatar")
        helper.copy("overwrite_existing_avatar")
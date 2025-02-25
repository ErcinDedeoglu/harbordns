import os
import logging
from cloudflare import Cloudflare

class CloudflareClient:
    _instance = None
    _client = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._client = Cloudflare(
                api_email=os.getenv("CLOUDFLARE_EMAIL"),
                api_key=os.getenv("CLOUDFLARE_API_KEY")
            )
            logging.info("Initialized Cloudflare API client")
            logging.debug(f"### API_KEY.length: {len(cls._client.api_key)} - API_KEY.last4: {cls._client.api_key[-4:]}")
        return cls._client
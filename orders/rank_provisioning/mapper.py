import json
import logging
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class UnknownWebRankError(Exception):
    pass


@dataclass(frozen=True)
class RankGrant:
    web_slug: str
    lp_group: str
    clear_existing: bool
    server: str
    display_name: str = ''


class RankMapper:
    def __init__(self, config_path=None):
        path = Path(config_path or getattr(settings, 'RANK_MAPPING_PATH', None))
        if not path or not path.exists():
            msg = f'Rank mapping file not found: {path}. Please set RANK_MAPPING_PATH in settings.'
            logger.critical(msg)
            raise ImproperlyConfigured(msg)
        with path.open(encoding='utf-8') as f:
            self.config = json.load(f)

    def resolve(self, web_slug: str, server_key: str | None = None) -> RankGrant:
        server_key = server_key or self.config.get('default_server', 'survival')
        slug = self.config.get('aliases', {}).get(web_slug, web_slug)

        servers = self.config.get('servers', {})
        if server_key not in servers:
            raise UnknownWebRankError(f"Unknown server key '{server_key}'")

        groups = servers[server_key].get('groups', {})
        if slug not in groups:
            raise UnknownWebRankError(f"No mapping for web rank slug '{web_slug}'")

        entry = groups[slug]
        return RankGrant(
            web_slug=slug,
            lp_group=entry['lp_group'],
            clear_existing=entry.get('clear_existing_parents', True),
            server=server_key,
            display_name=entry.get('display_name', slug),
        )

    def from_product(self, product, server_key: str | None = None) -> RankGrant:
        if getattr(product, 'luckperms_group', None):
            server_key = server_key or self.config.get('default_server', 'survival')
            return RankGrant(
                web_slug=product.slug,
                lp_group=product.luckperms_group,
                clear_existing=True,
                server=server_key,
                display_name=product.name,
            )
        return self.resolve(product.slug, server_key=server_key)
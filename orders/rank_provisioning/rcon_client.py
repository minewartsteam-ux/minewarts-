import logging
import re
from dataclasses import dataclass

from django.conf import settings
from mcrcon import MCRcon

logger = logging.getLogger(__name__)

MINECRAFT_USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]{1,16}$')


class RconError(Exception):
    def __init__(self, message, command=None, response=None):
        super().__init__(message)
        self.command = command
        self.response = response


class RconRetryableError(RconError):
    pass


def normalize_minecraft_username(username: str) -> str:
    if not username:
        raise RconError('نام کاربری ماینکرفت خالی است')
    normalized = username.strip()
    if not MINECRAFT_USERNAME_RE.match(normalized):
        raise RconError(
            f'نام کاربری ماینکرفت نامعتبر است: {normalized!r} '
            '(فقط حروف انگلیسی، اعداد و _ — حداکثر ۱۶ کاراکتر)'
        )
    return normalized


def format_luckperms_group(group: str) -> str:
    group = group.strip()
    if not group:
        raise RconError('نام گروه LuckPerms خالی است')
    # اگر گروه شامل کاراکترهای خاص باشد، با کوتیشن ایمن می‌کنیم
    if any(char in group for char in ' +&|;"\''):
        return f'"{group}"'
    return group


def format_luckperms_duration(months: int) -> str:
    if months < 1:
        raise RconError(f'مدت زمان نامعتبر: {months} ماه')
    return f'{months}mo'


@dataclass(frozen=True)
class RconConfig:
    host: str
    port: int
    password: str
    timeout: int

    @classmethod
    def from_settings(cls):
        password = getattr(settings, 'MINECRAFT_RCON_PASSWORD', '') or ''
        if not password:
            raise RconError(
                'RCON پیکربندی نشده است. MINECRAFT_RCON_PASSWORD را در environment تنظیم کنید.'
            )
        return cls(
            host=getattr(settings, 'MINECRAFT_RCON_HOST', '127.0.0.1'),
            port=int(getattr(settings, 'MINECRAFT_RCON_PORT', 25575)),
            password=password,
            timeout=int(getattr(settings, 'MINECRAFT_RCON_TIMEOUT', 10)),
        )


class RconClient:
    def __init__(self, config: RconConfig | None = None):
        self.config = config or RconConfig.from_settings()

    @property
    def enabled(self) -> bool:
        return bool(getattr(settings, 'MINECRAFT_RCON_PASSWORD', ''))

    def _run_command(self, mcr: MCRcon, command: str) -> str:
        logger.info('RCON command: %s', command)
        try:
            response = mcr.command(command)
        except Exception as exc:
            raise RconRetryableError(
                f'خطا در اجرای دستور RCON: {exc}',
                command=command,
            ) from exc
        response = (response or '').strip()
        logger.info('RCON response: %s', response)

        # بررسی وجود خطا در پاسخ
        lower_response = response.lower()
        error_keywords = ['error', 'not found', 'unknown', 'invalid', 'failed', 'exception']
        if any(kw in lower_response for kw in error_keywords):
            raise RconError(
                f'دستور با خطا مواجه شد: {response}',
                command=command,
                response=response,
            )
        # همچنین اگر پاسخ خالی باشد (برخی دستورات ممکن است خروجی ندهند) اما معمولاً موفقیت‌آمیز است.
        # ولی برای دستورات addtemp معمولاً پیام موفقیت برمی‌گردد.
        if not response:
            logger.warning('RCON command returned empty response, assuming success?')
        return response

    def provision_rank(self, payload: dict) -> dict:
        username = normalize_minecraft_username(payload['minecraft_username'])
        group = format_luckperms_group(payload['game_rank_group'])
        months = int(payload.get('duration_months', 1))
        duration = payload.get('duration_lp') or format_luckperms_duration(months)
        clear_existing = payload.get('clear_existing_parents', True)

        commands = []
        responses = {}

        try:
            with MCRcon(
                self.config.host,
                self.config.password,
                self.config.port,
                timeout=self.config.timeout,
            ) as mcr:
                if clear_existing:
                    cmd = f'lp user {username} parent clear'
                    responses['clear'] = self._run_command(mcr, cmd)
                    commands.append(cmd)

                cmd = f'lp user {username} parent addtemp {group} {duration}'
                responses['grant'] = self._run_command(mcr, cmd)
                commands.append(cmd)

        except ConnectionRefusedError as exc:
            raise RconRetryableError(
                f'اتصال RCON برقرار نشد ({self.config.host}:{self.config.port})',
            ) from exc
        except OSError as exc:
            raise RconRetryableError(f'خطای شبکه RCON: {exc}') from exc
        except TimeoutError as exc:
            raise RconRetryableError('زمان اتصال RCON تمام شد') from exc

        return {
            'status': 'applied',
            'via': 'rcon',
            'minecraft_username': username,
            'game_rank_group': payload['game_rank_group'],
            'duration': duration,
            'duration_months': months,
            'expires_at': payload.get('expires_at'),
            'commands': commands,
            'responses': responses,
        }
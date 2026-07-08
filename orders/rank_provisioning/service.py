import logging
import threading
from calendar import monthrange
from datetime import timedelta

from django.conf import settings
from django.db import transaction, connections
from django.utils import timezone

from shop.models import ProductMonth
from orders.models import Order, RankProvisionJob
from .mapper import RankMapper, UnknownWebRankError
from .rcon_client import (
    RconClient,
    RconError,
    RconRetryableError,
    format_luckperms_duration,
    normalize_minecraft_username,
)

logger = logging.getLogger(__name__)

RETRY_BACKOFF_MINUTES = (1, 5, 15, 60, 360)
DEFAULT_MAX_RETRIES = 5


def _compute_duration_months(rank_item):
    if rank_item.month_option_id:
        try:
            month_option = ProductMonth.objects.get(id=rank_item.month_option_id)
            return month_option.months
        except ProductMonth.DoesNotExist:
            logger.warning('ProductMonth not found for id %s, using default 1', rank_item.month_option_id)
            return 1
    return 1


def _compute_expires_at(months: int):
    now = timezone.now()
    target_month = now.month - 1 + months
    year = now.year + target_month // 12
    month = target_month % 12 + 1
    day = min(now.day, monthrange(year, month)[1])
    return now.replace(year=year, month=month, day=day)


def _resolve_minecraft_username(order):
    username = order.minecraft_username
    if order.user_id:
        try:
            profile = order.user.profile
            if profile.minecraft_username:
                username = profile.minecraft_username
        except Exception:
            pass
    return normalize_minecraft_username(username)


def _get_rank_item(order):
    # فرض می‌کنیم product_type = 'rank' و فقط یک آیتم رنک در سفارش وجود دارد
    for item in order.items.select_related('product').all():
        if getattr(item.product, 'product_type', '') == 'rank':
            return item
    return None


def _build_payload(order, rank_item, grant):
    months = _compute_duration_months(rank_item)
    expires_at = _compute_expires_at(months)
    username = _resolve_minecraft_username(order)
    duration_lp = format_luckperms_duration(months)

    return {
        'order_id': str(order.id),
        'minecraft_username': username,
        'web_rank_slug': grant.web_slug,
        'game_rank_group': grant.lp_group,
        'duration_months': months,
        'duration_lp': duration_lp,
        'expires_at': expires_at.isoformat(),
        'clear_existing_parents': grant.clear_existing,
        'action': 'grant_temp_parent',
    }


def _process_job_wrapper(job_id):
    try:
        process_rank_job(job_id)
    finally:
        connections.close_all()


def process_rank_job(job_id):
    try:
        job = RankProvisionJob.objects.select_related('order', 'order__user').get(id=job_id)
    except RankProvisionJob.DoesNotExist:
        logger.error('RankProvisionJob %s not found', job_id)
        return False

    # اگر قبلاً اعمال شده یا به حالت نهایی رسیده، نیازی به پردازش نیست
    if job.status in (RankProvisionJob.STATUS_APPLIED, RankProvisionJob.STATUS_FAILED, RankProvisionJob.STATUS_DEAD_LETTER):
        return job.status == RankProvisionJob.STATUS_APPLIED

    # اگر در حال پردازش است، از اجرای همزمان جلوگیری کنیم
    if job.status == RankProvisionJob.STATUS_PROCESSING:
        logger.warning('Job %s is already being processed, skipping', job.id)
        return False

    # اگر retry است ولی زمانش نرسیده، صرف‌نظر کن
    if job.status == RankProvisionJob.STATUS_RETRY and job.next_retry_at and job.next_retry_at > timezone.now():
        return False

    order = job.order
    # قفل optimistic با به‌روزرسانی وضعیت
    # استفاده از select_for_update? اما اینجا ساده می‌گیریم
    job.status = RankProvisionJob.STATUS_PROCESSING
    job.attempts += 1
    job.save(update_fields=['status', 'attempts', 'updated'])

    payload = dict(job.payload)
    client = RconClient()
    max_retries = getattr(settings, 'RANK_MAX_RETRIES', DEFAULT_MAX_RETRIES)

    try:
        if not client.enabled:
            raise RconError(
                'RCON پیکربندی نشده است. MINECRAFT_RCON_PASSWORD را در environment تنظیم کنید.'
            )

        rank_item = _get_rank_item(order)
        if rank_item:
            mapper = RankMapper()
            grant = mapper.from_product(rank_item.product)
            payload = _build_payload(order, rank_item, grant)
        else:
            # اگر آیتم رنکی وجود نداشت، سفارش را بدون خطا موفق در نظر می‌گیریم
            logger.info('Order %s has no rank item, marking as applied', order.id)
            job.status = RankProvisionJob.STATUS_APPLIED
            job.rcon_response = {'note': 'No rank item to provision'}
            job.last_error = ''
            job.next_retry_at = None
            job.save(update_fields=['status', 'rcon_response', 'last_error', 'next_retry_at', 'updated'])
            order.rank_applied = True
            order.rank_error = ''
            order.save(update_fields=['rank_applied', 'rank_error', 'updated'])
            return True

        result = client.provision_rank(payload)

        job.status = RankProvisionJob.STATUS_APPLIED
        job.rcon_response = result
        job.last_error = ''
        job.next_retry_at = None
        job.save(update_fields=['status', 'rcon_response', 'last_error', 'next_retry_at', 'updated'])

        order.rank_applied = True
        order.rank_error = ''
        order.save(update_fields=['rank_applied', 'rank_error', 'updated'])
        logger.info('Rank applied for order %s via RCON job %s', order.id, job.id)
        return True

    except RconRetryableError as exc:
        job.last_error = str(exc)
        job.rcon_response = {'error': str(exc), 'command': exc.command}

        if job.attempts >= max_retries:
            job.status = RankProvisionJob.STATUS_DEAD_LETTER
            order.rank_error = f'Max retries exceeded: {exc}'
            order.save(update_fields=['rank_error', 'updated'])
        else:
            backoff_idx = min(job.attempts - 1, len(RETRY_BACKOFF_MINUTES) - 1)
            minutes = RETRY_BACKOFF_MINUTES[backoff_idx]
            job.status = RankProvisionJob.STATUS_RETRY
            job.next_retry_at = timezone.now() + timedelta(minutes=minutes)

        job.save(update_fields=['status', 'last_error', 'rcon_response', 'next_retry_at', 'updated'])
        logger.warning('Rank job %s scheduled for retry: %s', job.id, exc)
        return False

    except (RconError, UnknownWebRankError) as exc:
        job.status = RankProvisionJob.STATUS_FAILED
        job.last_error = str(exc)
        job.save(update_fields=['status', 'last_error', 'updated'])
        order.rank_error = str(exc)
        order.save(update_fields=['rank_error', 'updated'])
        logger.error('Rank job %s failed permanently: %s', job.id, exc)
        return False

    except Exception as exc:
        # خطای غیرمنتظره – به حالت retry با بک‌آف اولیه
        job.status = RankProvisionJob.STATUS_RETRY
        job.last_error = str(exc)
        job.next_retry_at = timezone.now() + timedelta(minutes=RETRY_BACKOFF_MINUTES[0])
        job.save(update_fields=['status', 'last_error', 'next_retry_at', 'updated'])
        logger.exception('Unexpected error in rank job %s', job.id)
        return False


def enqueue_rank_provision(order_id):
    order = Order.objects.select_related('user').prefetch_related('items__product').get(id=order_id)
    rank_item = _get_rank_item(order)

    if not rank_item:
        # بدون آیتم رنک، نیازی به پردازش نیست
        order.rank_applied = True
        order.save(update_fields=['rank_applied', 'updated'])
        logger.info('Order %s has no rank item, marked applied', order.id)
        return None

    try:
        _resolve_minecraft_username(order)
    except RconError as exc:
        order.rank_error = str(exc)
        order.save(update_fields=['rank_error', 'updated'])
        return None

    mapper = RankMapper()
    grant = mapper.from_product(rank_item.product)
    payload = _build_payload(order, rank_item, grant)
    idempotency_key = f'order-{order.id}-rank-{grant.lp_group}-v1'

    existing = RankProvisionJob.objects.filter(idempotency_key=idempotency_key).first()
    if existing:
        # اگر در حال پردازش است، دوباره اجرا نکن
        if existing.status == RankProvisionJob.STATUS_PROCESSING:
            logger.info('Job %s is already processing, not starting another', existing.id)
            return existing
        # اگر هنوز انجام نشده یا باید retry شود، یک thread جدید شروع کن
        if existing.status not in (RankProvisionJob.STATUS_APPLIED, RankProvisionJob.STATUS_FAILED, RankProvisionJob.STATUS_DEAD_LETTER):
            threading.Thread(target=_process_job_wrapper, args=(existing.id,), daemon=True).start()
        return existing

    with transaction.atomic():
        job = RankProvisionJob.objects.create(
            order=order,
            idempotency_key=idempotency_key,
            payload=payload,
            status=RankProvisionJob.STATUS_PENDING,
        )

    threading.Thread(target=_process_job_wrapper, args=(job.id,), daemon=True).start()
    return job


def process_pending_rank_jobs(limit=50):
    from django.db.models import Q

    now = timezone.now()
    jobs = RankProvisionJob.objects.filter(
        Q(status=RankProvisionJob.STATUS_PENDING)
        | Q(status=RankProvisionJob.STATUS_RETRY, next_retry_at__lte=now)
        | Q(status=RankProvisionJob.STATUS_RETRY, next_retry_at__isnull=True)
    ).order_by('next_retry_at', 'created')[:limit]

    processed = 0
    for job in jobs:
        if process_rank_job(job.id):
            processed += 1
    return processed
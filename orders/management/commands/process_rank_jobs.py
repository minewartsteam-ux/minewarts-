from django.core.management.base import BaseCommand

from orders.rank_provisioning import process_pending_rank_jobs


class Command(BaseCommand):
    help = 'Process pending rank provision jobs (run via cron every 1-5 minutes)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of jobs to process in one run',
        )

    def handle(self, *args, **options):
        applied = process_pending_rank_jobs(limit=options['limit'])
        self.stdout.write(self.style.SUCCESS(f'Processed rank jobs; {applied} applied successfully.'))

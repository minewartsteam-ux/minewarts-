"""
Management command for fixing invalid balance values in WartCoin
"""
from django.core.management.base import BaseCommand
from django.db import connection
from decimal import Decimal, InvalidOperation


class Command(BaseCommand):
    help = 'Fix invalid balance values in WartCoin'

    def handle(self, *args, **options):
        self.stdout.write('Checking and fixing invalid balances...')
        
        fixed_count = 0
        
        try:
            with connection.cursor() as cursor:
                # Get all records
                cursor.execute("SELECT id, balance FROM accounts_wartcoin")
                records = cursor.fetchall()
                
                for record_id, balance_value in records:
                    try:
                        # Try to convert to Decimal
                        if balance_value is None or balance_value == '':
                            # Fix NULL or empty
                            cursor.execute(
                                "UPDATE accounts_wartcoin SET balance = 0.00 WHERE id = ?",
                                [record_id]
                            )
                            fixed_count += 1
                        else:
                            # Try to convert to Decimal to validate
                            try:
                                Decimal(str(balance_value))
                            except (InvalidOperation, ValueError, TypeError):
                                # Invalid value, fix it
                                cursor.execute(
                                    "UPDATE accounts_wartcoin SET balance = 0.00 WHERE id = ?",
                                    [record_id]
                                )
                                fixed_count += 1
                    except Exception as e:
                        # If anything fails, set to 0.00
                        try:
                            cursor.execute(
                                "UPDATE accounts_wartcoin SET balance = 0.00 WHERE id = ?",
                                [record_id]
                            )
                            fixed_count += 1
                        except Exception:
                            pass
                
                connection.commit()
                
                if fixed_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'Fixed {fixed_count} records')
                    )
                else:
                    self.stdout.write(self.style.SUCCESS('All records are valid'))
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )


#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ایجاد دستی جداول تیکت در دیتابیس
این اسکریپت را اجرا کنید: python create_tables_manual.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
django.setup()

from django.db import connection
from django.utils import timezone

def create_tables():
    cursor = connection.cursor()
    
    try:
        print("=" * 50)
        print("🔨 ایجاد جداول تیکت...")
        print("=" * 50)
        
        # 1. ایجاد جدول accounts_supportticket
        print("\n1️⃣ ایجاد جدول accounts_supportticket...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts_supportticket (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject VARCHAR(255) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'open',
                created DATETIME NOT NULL,
                updated DATETIME NOT NULL,
                user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE
            )
        """)
        print("   ✅ انجام شد")
        
        # 2. ایجاد جدول accounts_supportmessage
        print("\n2️⃣ ایجاد جدول accounts_supportmessage...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts_supportmessage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                is_staff BOOLEAN NOT NULL DEFAULT 0,
                message TEXT NOT NULL,
                created DATETIME NOT NULL,
                ticket_id INTEGER NOT NULL REFERENCES accounts_supportticket(id) ON DELETE CASCADE,
                sender_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL
            )
        """)
        print("   ✅ انجام شد")
        
        # 3. ایجاد جدول ManyToMany برای assigned_admins
        print("\n3️⃣ ایجاد جدول accounts_supportticket_assigned_admins...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts_supportticket_assigned_admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supportticket_id INTEGER NOT NULL REFERENCES accounts_supportticket(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
                UNIQUE(supportticket_id, user_id)
            )
        """)
        print("   ✅ انجام شد")
        
        # 4. ایجاد Index ها
        print("\n4️⃣ ایجاد Index ها...")
        cursor.execute("CREATE INDEX IF NOT EXISTS accounts_supportticket_user_id ON accounts_supportticket(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS accounts_supportmessage_ticket_id ON accounts_supportmessage(ticket_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS accounts_supportmessage_sender_id ON accounts_supportmessage(sender_id)")
        print("   ✅ انجام شد")
        
        # 5. ثبت migration در django_migrations
        print("\n5️⃣ ثبت migration در django_migrations...")
        applied_time = timezone.now()
        cursor.execute("""
            INSERT OR IGNORE INTO django_migrations (app, name, applied)
            VALUES (?, ?, ?)
        """, ('accounts', '0001_initial', applied_time))
        print("   ✅ انجام شد")
        
        connection.commit()
        
        print("\n" + "=" * 50)
        print("✅ همه جداول با موفقیت ایجاد شدند!")
        print("=" * 50)
        
        # تست
        print("\n🧪 تست...")
        from accounts.models import SupportTicket, SupportMessage
        ticket_count = SupportTicket.objects.count()
        message_count = SupportMessage.objects.count()
        print(f"   ✅ SupportTicket count: {ticket_count}")
        print(f"   ✅ SupportMessage count: {message_count}")
        print("\n🎉 همه چیز آماده است!")
        
    except Exception as e:
        connection.rollback()
        print("\n" + "=" * 50)
        print(f"❌ خطا: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = create_tables()
    if success:
        print("\n✅ می‌توانید حالا سایت را اجرا کنید!")
    else:
        print("\n❌ لطفاً خطا را بررسی کنید و دوباره تلاش کنید.")

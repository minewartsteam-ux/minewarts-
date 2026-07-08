# orders/payment_gateway.py
import requests
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ZarinpalPayment:
    def __init__(self):
        # ✅ مرچنت آیدی صحیح برای سندباکس
        self.merchant_id = settings.ZARINPAL_MERCHANT_ID
        self.sandbox = settings.ZARINPAL_SANDBOX
        
        if self.sandbox:
            self.request_url = 'https://sandbox.zarinpal.com/pg/v4/payment/request.json'
            self.verify_url = 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json'
        else:
            self.request_url = 'https://api.zarinpal.com/pg/v4/payment/request.json'
            self.verify_url = 'https://api.zarinpal.com/pg/v4/payment/verify.json'
    
    def send_request(self, amount, description, callback_url, email=None, mobile=None):
        """
        ارسال درخواست به زرین‌پال
        
        Args:
            amount: مبلغ به **ریال** (تومان * 10)
            description: توضیحات تراکنش
            callback_url: آدرس بازگشت
            email: ایمیل کاربر (اختیاری)
            mobile: موبایل کاربر (اختیاری)
        """
        
        # ✅ داده‌های ارسالی به زرین‌پال
        data = {
            "merchant_id": self.merchant_id,
            "amount": int(amount),  # ریال (تومان * 10)
            "callback_url": callback_url,
            "description": description[:255],  # حداکثر ۲۵۵ کاراکتر
            "metadata": {
                "email": email or "test@example.com",
                "mobile": mobile or "09123456789"
            }
        }
        
        # لاگ برای دیباگ
        logger.info(f"📤 ارسال درخواست به زرین‌پال:")
        logger.info(f"   - Merchant ID: {self.merchant_id}")
        logger.info(f"   - Amount (Rial): {amount:,}")
        logger.info(f"   - Callback: {callback_url}")
        
        try:
            response = requests.post(
                self.request_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            logger.info(f"📥 پاسخ زرین‌پال: Status {response.status_code}")
            logger.info(f"   - Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                result = response.json()
                
                # بررسی خطاهای زرین‌پال
                errors = result.get('errors')
                if errors:
                    error_code = errors.get('code')
                    error_message = errors.get('message')
                    
                    logger.error(f"❌ خطای زرین‌پال: {error_code} - {error_message}")
                    
                    # خطاهای رایج
                    error_messages = {
                        -1: 'اطلاعات ارسالی ناقص است',
                        -2: 'مرچنت آیدی نامعتبر است (برای سندباکس از 00000000-0000-0000-0000-000000000000 استفاده کنید)',
                        -3: 'مبلغ باید بیشتر از ۰ باشد',
                        -4: 'آدرس بازگشت نامعتبر است',
                        -5: 'توضیحات تراکنش نمی‌تواند خالی باشد',
                        -6: 'ایمیل یا موبایل نامعتبر است',
                        -7: 'مبلغ بیشتر از حد مجاز است',
                        -8: 'درخواست تکراری است',
                        -9: 'خطای داخلی زرین‌پال',
                        -10: 'تراکنش در صف پردازش است',
                    }
                    
                    return {
                        'status': 'error',
                        'code': error_code,
                        'message': error_messages.get(error_code, error_message or 'خطای نامشخص')
                    }
                
                # بررسی موفقیت
                data_result = result.get('data', {})
                if data_result.get('code') == 100:
                    authority = data_result.get('authority')
                    payment_url = f"https://{'sandbox.' if self.sandbox else ''}zarinpal.com/pg/StartPay/{authority}/"
                    
                    return {
                        'status': 'success',
                        'authority': authority,
                        'payment_url': payment_url,
                        'ref_id': None
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f"کد خطا: {data_result.get('code')}",
                        'code': data_result.get('code')
                    }
            
            else:
                # خطای HTTP غیر از ۲۰۰
                logger.error(f"❌ خطای HTTP: {response.status_code}")
                logger.error(f"   - Response: {response.text}")
                
                return {
                    'status': 'error',
                    'message': f'خطا در ارتباط با درگاه (کد {response.status_code})'
                }
                
        except requests.exceptions.Timeout:
            logger.error("❌ خطا: Timeout در ارتباط با زرین‌پال")
            return {
                'status': 'error',
                'message': 'ارتباط با درگاه پرداخت زمان‌بر شد. لطفاً دوباره تلاش کنید.'
            }
        except requests.exceptions.ConnectionError:
            logger.error("❌ خطا: Connection Error در ارتباط با زرین‌پال")
            return {
                'status': 'error',
                'message': 'ارتباط با درگاه پرداخت برقرار نشد. لطفاً دوباره تلاش کنید.'
            }
        except Exception as e:
            logger.error(f"❌ خطای غیرمنتظره: {str(e)}")
            return {
                'status': 'error',
                'message': f'خطای غیرمنتظره: {str(e)}'
            }
    
    def verify_payment(self, amount, authority):
        """
        تایید پرداخت
        
        Args:
            amount: مبلغ به **ریال** (تومان * 10)
            authority: کد مرجع از زرین‌پال
        """
        
        data = {
            "merchant_id": self.merchant_id,
            "amount": int(amount),  # ریال (تومان * 10)
            "authority": authority
        }
        
        logger.info(f"📤 تایید پرداخت: Authority={authority}, Amount={amount:,}")
        
        try:
            response = requests.post(
                self.verify_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            logger.info(f"📥 پاسخ تایید: Status {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                errors = result.get('errors')
                if errors:
                    error_code = errors.get('code')
                    error_message = errors.get('message')
                    
                    logger.error(f"❌ خطای تایید: {error_code} - {error_message}")
                    return {
                        'status': 'error',
                        'message': f'خطای {error_code}: {error_message}'
                    }
                
                data_result = result.get('data', {})
                if data_result.get('code') == 100:
                    return {
                        'status': 'success',
                        'ref_id': data_result.get('ref_id'),
                        'card_pan': data_result.get('card_pan'),
                        'card_hash': data_result.get('card_hash'),
                        'fee_type': data_result.get('fee_type'),
                        'fee': data_result.get('fee')
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f"کد خطا: {data_result.get('code')}"
                    }
            else:
                return {
                    'status': 'error',
                    'message': f'خطا در تایید پرداخت (کد {response.status_code})'
                }
                
        except Exception as e:
            logger.error(f"❌ خطا در تایید پرداخت: {str(e)}")
            return {
                'status': 'error',
                'message': f'خطا در تایید پرداخت: {str(e)}'
            }
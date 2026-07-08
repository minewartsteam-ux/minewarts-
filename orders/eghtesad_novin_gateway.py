"""
ماژول پرداخت واقعی با درگاه بانک اقتصاد نوین
این ماژول به درگاه واقعی بانک اقتصاد نوین متصل می‌شود و پرداخت واقعی انجام می‌دهد
"""
import requests
from django.conf import settings
import logging
import hashlib
import hmac
import json
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class EghtesadNovinPayment:
    """
    کلاس پرداخت با درگاه بانک اقتصاد نوین
    """
    def __init__(self):
        self.merchant_id = settings.EGHTESAD_NOVIN_MERCHANT_ID
        self.terminal_id = settings.EGHTESAD_NOVIN_TERMINAL_ID
        self.terminal_key = settings.EGHTESAD_NOVIN_TERMINAL_KEY
        self.request_url = settings.EGHTESAD_NOVIN_REQUEST_URL
        self.verify_url = settings.EGHTESAD_NOVIN_VERIFY_URL
        self.payment_url = settings.EGHTESAD_NOVIN_PAYMENT_URL
        
        # بررسی صحت تنظیمات
        if not self.merchant_id or self.merchant_id == 'your-merchant-id-here':
            logger.warning('⚠️ Merchant ID بانک اقتصاد نوین تنظیم نشده است!')
        if not self.terminal_id or self.terminal_id == 'your-terminal-id-here':
            logger.warning('⚠️ Terminal ID بانک اقتصاد نوین تنظیم نشده است!')
        if not self.terminal_key or self.terminal_key == 'your-terminal-key-here':
            logger.warning('⚠️ Terminal Key بانک اقتصاد نوین تنظیم نشده است!')
    
    def _generate_signature(self, data):
        """
        تولید امضای امنیتی برای درخواست
        روش: SHA256 hash از داده‌های مرتب شده + Terminal Key
        """
        try:
            # حذف SignData از داده‌ها برای محاسبه امضا
            data_for_sign = {k: v for k, v in data.items() if k != 'SignData' and v is not None}
            
            # مرتب‌سازی داده‌ها بر اساس کلید
            sorted_data = sorted(data_for_sign.items())
            
            # ساخت رشته داده
            data_string = '&'.join([f"{key}={value}" for key, value in sorted_data])
            data_string += f"&key={self.terminal_key}"
            
            # تولید hash با SHA256
            signature = hashlib.sha256(data_string.encode('utf-8')).hexdigest()
            return signature.upper()
        except Exception as e:
            logger.error(f'خطا در تولید امضا: {str(e)}')
            return None
    
    def send_request(self, amount, description, callback_url, order_id, email=None, mobile=None):
        """
        ارسال درخواست پرداخت به درگاه بانک اقتصاد نوین با امنیت بالا
        """
        # اعتبارسنجی ورودی‌ها
        try:
            amount_int = int(amount)
            if amount_int <= 0:
                return {
                    'status': 'error',
                    'message': 'مبلغ پرداخت نامعتبر است'
                }
        except (ValueError, TypeError):
            return {
                'status': 'error',
                'message': 'مبلغ پرداخت نامعتبر است'
            }
        
        # بررسی تنظیمات
        if not self.merchant_id or self.merchant_id == 'your-merchant-id-here':
            return {
                'status': 'error',
                'message': '⚠️ Merchant ID تنظیم نشده است! لطفاً تنظیمات درگاه را کامل کنید.'
            }
        
        if not self.terminal_id or self.terminal_id == 'your-terminal-id-here':
            return {
                'status': 'error',
                'message': '⚠️ Terminal ID تنظیم نشده است! لطفاً تنظیمات درگاه را کامل کنید.'
            }
        
        if not self.terminal_key or self.terminal_key == 'your-terminal-key-here':
            return {
                'status': 'error',
                'message': '⚠️ Terminal Key تنظیم نشده است! لطفاً تنظیمات درگاه را کامل کنید.'
            }
        
        # آماده‌سازی داده‌ها (بدون SignData)
        data = {
            'MerchantID': str(self.merchant_id),
            'TerminalID': str(self.terminal_id),
            'Amount': amount_int,
            'OrderId': str(order_id),
            'LocalDateTime': self._get_local_datetime(),
            'ReturnUrl': callback_url,
        }
        
        # اضافه کردن اطلاعات اختیاری
        if description:
            data['AdditionalData'] = str(description)[:255]
        if email:
            data['Email'] = str(email)[:100]
        if mobile:
            data['MobileNo'] = str(mobile)[:11]
        
        # تولید امضا
        signature = self._generate_signature(data)
        if not signature:
            return {
                'status': 'error',
                'message': 'خطا در تولید امضای امنیتی'
            }
        
        # اضافه کردن امضا به داده‌ها
        data['SignData'] = signature
        
        try:
            # ارسال درخواست به درگاه
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Django-EghtesadNovin-Gateway/1.0'
            }
            
            response = requests.post(
                self.request_url,
                json=data,
                headers=headers,
                timeout=20,
                verify=True,  # بررسی SSL certificate
                allow_redirects=False
            )
            
            # بررسی status code
            if response.status_code != 200:
                logger.error(f'خطا در ارتباط با درگاه: Status Code {response.status_code}')
                return {
                    'status': 'error',
                    'message': f'خطا در ارتباط با درگاه پرداخت (کد: {response.status_code})'
                }
            
            result = response.json()
            
            # بررسی پاسخ - ممکن است فرمت‌های مختلف داشته باشد
            # فرمت 1: ResCode و Token
            if result.get('ResCode') == '0' or result.get('resCode') == '0' or result.get('status') == 'success':
                token = result.get('Token') or result.get('token') or result.get('Authority')
                if token:
                    payment_url = f"{self.payment_url}?Token={token}"
                    return {
                        'status': 'success',
                        'token': token,
                        'payment_url': payment_url,
                        'res_code': result.get('ResCode') or result.get('resCode', '0'),
                        'message': result.get('Description') or result.get('description') or result.get('message', 'درخواست با موفقیت ثبت شد')
                    }
                else:
                    return {
                        'status': 'error',
                        'message': 'خطا در دریافت Token پرداخت'
                    }
            # فرمت 2: code و data
            elif result.get('data', {}).get('code') == 100:
                token = result.get('data', {}).get('authority') or result.get('data', {}).get('token')
                if token:
                    payment_url = f"{self.payment_url}?Token={token}"
                    return {
                        'status': 'success',
                        'token': token,
                        'payment_url': payment_url,
                        'res_code': '0',
                        'message': 'درخواست با موفقیت ثبت شد'
                    }
            else:
                error_message = result.get('Description') or result.get('description') or result.get('message') or result.get('errors', {}).get('message', 'خطا در اتصال به درگاه پرداخت')
                return {
                    'status': 'error',
                    'message': f'❌ {error_message}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'message': 'زمان اتصال به درگاه پرداخت به پایان رسید. لطفاً دوباره تلاش کنید.'
            }
        except requests.exceptions.RequestException as e:
            logger.error(f'خطا در ارتباط با درگاه: {str(e)}')
            return {
                'status': 'error',
                'message': f'خطا در ارتباط با درگاه پرداخت: {str(e)}'
            }
        except Exception as e:
            logger.error(f'خطای نامشخص: {str(e)}')
            return {
                'status': 'error',
                'message': f'خطای نامشخص: {str(e)}'
            }
    
    def verify_payment(self, token, amount, order_id):
        """
        بررسی صحت پرداخت با امنیت بالا
        """
        # اعتبارسنجی ورودی‌ها
        if not token or len(token) < 10:
            return {
                'status': 'error',
                'message': 'Token پرداخت نامعتبر است'
            }
        
        try:
            amount_int = int(amount)
            if amount_int <= 0:
                return {
                    'status': 'error',
                    'message': 'مبلغ پرداخت نامعتبر است'
                }
        except (ValueError, TypeError):
            return {
                'status': 'error',
                'message': 'مبلغ پرداخت نامعتبر است'
            }
        
        # آماده‌سازی داده‌ها (بدون SignData)
        data = {
            'MerchantID': str(self.merchant_id),
            'TerminalID': str(self.terminal_id),
            'Token': str(token),
        }
        
        # تولید امضا
        signature = self._generate_signature(data)
        if not signature:
            return {
                'status': 'error',
                'message': 'خطا در تولید امضای امنیتی'
            }
        
        # اضافه کردن امضا به داده‌ها
        data['SignData'] = signature
        
        try:
            # ارسال درخواست بررسی
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Django-EghtesadNovin-Gateway/1.0'
            }
            
            response = requests.post(
                self.verify_url,
                json=data,
                headers=headers,
                timeout=20,
                verify=True,
                allow_redirects=False
            )
            
            # بررسی status code
            if response.status_code != 200:
                logger.error(f'خطا در بررسی پرداخت: Status Code {response.status_code}')
                return {
                    'status': 'error',
                    'message': f'خطا در بررسی پرداخت (کد: {response.status_code})'
                }
            
            result = response.json()
            
            # بررسی پاسخ - ممکن است فرمت‌های مختلف داشته باشد
            # فرمت 1: ResCode
            if result.get('ResCode') == '0' or result.get('resCode') == '0' or result.get('status') == 'success':
                ref_id = result.get('SystemTraceNo') or result.get('RetrivalRefNo') or result.get('RefNum') or result.get('ref_id') or token
                return {
                    'status': 'success',
                    'ref_id': ref_id,
                    'res_code': result.get('ResCode') or result.get('resCode', '0'),
                    'message': 'پرداخت با موفقیت انجام شد'
                }
            # فرمت 2: code و data
            elif result.get('data', {}).get('code') == 100:
                ref_id = result.get('data', {}).get('ref_id') or result.get('data', {}).get('refId') or token
                return {
                    'status': 'success',
                    'ref_id': ref_id,
                    'res_code': '0',
                    'message': 'پرداخت با موفقیت انجام شد'
                }
            else:
                error_message = result.get('Description') or result.get('description') or result.get('message') or result.get('errors', {}).get('message', 'پرداخت ناموفق بود')
                return {
                    'status': 'error',
                    'message': f'❌ {error_message}'
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'message': 'زمان بررسی پرداخت به پایان رسید. لطفاً دوباره تلاش کنید.'
            }
        except requests.exceptions.RequestException as e:
            logger.error(f'خطا در بررسی پرداخت: {str(e)}')
            return {
                'status': 'error',
                'message': f'خطا در بررسی پرداخت: {str(e)}'
            }
        except Exception as e:
            logger.error(f'خطای نامشخص: {str(e)}')
            return {
                'status': 'error',
                'message': f'خطای نامشخص: {str(e)}'
            }
    
    def _get_local_datetime(self):
        """
        دریافت تاریخ و زمان محلی به فرمت مورد نیاز درگاه
        """
        from django.utils import timezone
        from datetime import datetime
        
        now = timezone.now()
        # فرمت: YYYYMMDDHHMMSS
        return now.strftime('%Y%m%d%H%M%S')


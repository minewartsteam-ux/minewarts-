from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def split_enchantments(enchantments_text):
    """
    تقسیم کردن انچنت‌ها به خطوط جداگانه
    """
    if not enchantments_text:
        return []
    return [line.strip() for line in enchantments_text.strip().split('\n') if line.strip()]


@register.filter
def parse_rank_specifications(specifications_text):
    """
    پارس کردن specifications رنک به فرمت جدول
    فرمت ورودی: 
    fly : tick --
    spawner : cross --
    
    خروجی: HTML جدول با تیک سبز یا ضربدر قرمز
    """
    if not specifications_text:
        return ""
    
    rows = []
    lines = specifications_text.strip().split('--')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # پارس کردن فرمت: item : tick/cross
        if ':' in line:
            parts = line.split(':', 1)
            item = parts[0].strip()
            status = parts[1].strip().lower()
            
            # تشخیص tick یا cross
            if status == 'tick':
                icon = '<span style="color: #4CAF50; font-size: 1.5rem; font-weight: bold;">✓</span>'
            elif status == 'cross' or status == 'zarb' or status == 'zarbdar':
                icon = '<span style="color: #f44336; font-size: 1.5rem; font-weight: bold;">✗</span>'
            else:
                icon = '<span style="color: #999;">—</span>'
            
            rows.append({
                'item': item,
                'icon': icon
            })
    
    if not rows:
        return ""
    
    # ساخت HTML جدول
    html = '<table style="width: 100%; border-collapse: collapse; margin: 0;">'
    html += '<tbody>'
    
    for row in rows:
        html += '<tr style="border-top: 1px solid rgba(255,255,255,0.1);">'
        html += f'<td style="padding: 12px; text-align: right; font-weight: bold; color: var(--text-light); width: 70%;">{row["item"]}</td>'
        html += f'<td style="padding: 12px; text-align: center; width: 30%;">{row["icon"]}</td>'
        html += '</tr>'
    
    html += '</tbody>'
    html += '</table>'
    
    return mark_safe(html)


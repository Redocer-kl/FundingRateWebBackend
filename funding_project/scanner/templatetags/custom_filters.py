from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Позволяет получать значение из словаря по динамическому ключу.
    Использование в шаблоне: {{ grouped_data|get_item:symbol }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter(name='split')
def split(value, arg):
    """
    Разбивает строку в список по разделителю.
    Использование в шаблоне: {% for p in '1d,3d,7d'|split:',' %}
    """
    return value.split(arg)

@register.filter(name='abs_val')
def abs_val(value):
    """
    Возвращает абсолютное значение (число без минуса).
    Полезно для отображения разницы или если нужно просто число.
    """
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value

@register.filter(name='multiply')
def multiply(value, arg):
    """
    Простое умножение в шаблоне.
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
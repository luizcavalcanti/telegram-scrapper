from django import template

register = template.Library()


@register.filter
def pretty_user(user):
    return str(type(user))
    # result = ""
    # for item in iterable:
        # result += item[0]

    # return result

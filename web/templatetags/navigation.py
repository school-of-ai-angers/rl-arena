from django import template
from core.models import Environment

register = template.Library()


@register.inclusion_tag('web/navigation.html', takes_context=True)
def navigation(context):
    """
    Renders the navigation bar with:
    - a link to home
    - a link to each environment
    - if disconnected, links to login and account creation.
    - if connected, links to profile and logout
    """
    envs = Environment.objects.all().order_by('name').values('name', 'slug')
    return {
        'environments': envs,
        'user': context['request'].user,
        'active_environment_slug': context.get('active_environment_slug')
    }

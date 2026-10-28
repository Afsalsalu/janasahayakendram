from django.conf import settings


def runtime_config(request):
    return {
        "MAPBOX_ACCESS_TOKEN": settings.MAPBOX_ACCESS_TOKEN,
    }

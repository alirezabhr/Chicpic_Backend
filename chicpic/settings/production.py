from chicpic.settings.base import *

import sentry_sdk

sentry_sdk.init(
    dsn=config('SENTRY_DSN'),
    environment=config('SENTRY_ENVIRONMENT'),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.zoho.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
SERVER_EMAIL = EMAIL_HOST_USER
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

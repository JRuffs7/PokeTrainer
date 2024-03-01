import logging
from logging.config import dictConfig


LOGGING_CONFIG = {
    'version': 1,
    'disabled_existing_loggers': False,
    'formatters': {
        'verbose': { 'format': '%(asctime)s - %(levelname)-10s: %(message)s' },
        'standard': { 'format': '%(levelname)-10s - %(name)-15s : %(message)s' },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'discord': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/discord.log',
            'mode': 'w',
            'formatter': 'verbose',
        },
        'error': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/errors.log',
            'mode': 'w',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        'error': { 'handlers': ['error'], 'level': 'INFO', 'propagate': False },
        'discord': { 'handlers': ['discord'], 'level': 'INFO', 'propagate': False },
        'console': { 'handlers': ['console'], 'level': 'DEBUG', 'propagate': False }
    },
}

dictConfig(LOGGING_CONFIG)


def override_loglevels():
	logging.getLogger('discord.client').setLevel(logging.WARNING)
	logging.getLogger('discord.gateway').setLevel(logging.WARNING)
	logging.getLogger('discord.http').setLevel(logging.WARNING)
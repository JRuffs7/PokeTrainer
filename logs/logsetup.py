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
            'mode': 'a',
            'formatter': 'verbose',
        },
        'battle': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/battle.log',
            'mode': 'a',
            'formatter': 'verbose',
        },
        'capture': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/capture.log',
            'mode': 'a',
            'formatter': 'verbose',
        },
        'error': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/errors.log',
            'mode': 'w',
            'formatter': 'verbose',
        },
        'event': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/event.log',
            'mode': 'a',
            'formatter': 'verbose',
        }
    },
    'loggers': {
        'console': { 'handlers': ['console'], 'level': 'DEBUG', 'propagate': False },
        'discord': { 'handlers': ['discord'], 'level': 'INFO', 'propagate': False },
        'capture': { 'handlers': ['capture'], 'level': 'INFO', 'propagate': False },
        'battle': { 'handlers': ['battle'], 'level': 'INFO', 'propagate': False },
        'error': { 'handlers': ['error'], 'level': 'INFO', 'propagate': False },
        'event': { 'handlers': ['event'], 'level': 'INFO', 'propagate': False }
    },
}

dictConfig(LOGGING_CONFIG)


def override_loglevels():
	logging.getLogger('discord.client').setLevel(logging.WARNING)
	logging.getLogger('discord.gateway').setLevel(logging.WARNING)
	logging.getLogger('discord.http').setLevel(logging.WARNING)
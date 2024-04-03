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
        'command': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/command.log',
            'mode': 'a+',
            'formatter': 'verbose',
			'encoding': 'utf-8'
        },
        'discord': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/discord.log',
            'mode': 'w+',
            'formatter': 'verbose',
			'encoding': 'utf-8'
        },
        'battle': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/battle.log',
            'mode': 'a+',
            'formatter': 'verbose',
			'encoding': 'utf-8'
        },
        'capture': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/capture.log',
            'mode': 'a+',
            'formatter': 'verbose',
			'encoding': 'utf-8'
        },
        'error': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/errors.log',
            'mode': 'w+',
            'formatter': 'verbose',
			'encoding': 'utf-8'
        },
        'event': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/event.log',
            'mode': 'a+',
            'formatter': 'verbose',
			'encoding': 'utf-8'
        },
        'debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/debug.log',
            'mode': 'w+',
            'formatter': 'verbose',
			'encoding': 'utf-8'
        }
    },
    'loggers': {
        'command': { 'handlers': ['command'], 'level': 'INFO', 'propagate': False },
        'discord': { 'handlers': ['discord'], 'level': 'INFO', 'propagate': False },
        'capture': { 'handlers': ['capture'], 'level': 'INFO', 'propagate': False },
        'battle': { 'handlers': ['battle'], 'level': 'INFO', 'propagate': False },
        'error': { 'handlers': ['error'], 'level': 'INFO', 'propagate': False },
        'event': { 'handlers': ['event'], 'level': 'INFO', 'propagate': False },
        'debug': { 'handlers': ['debug'], 'level': 'DEBUG', 'propagate': False }
    },
}

dictConfig(LOGGING_CONFIG)


def override_loglevels():
	logging.getLogger('discord.client').setLevel(logging.WARNING)
	logging.getLogger('discord.gateway').setLevel(logging.WARNING)
	logging.getLogger('discord.http').setLevel(logging.WARNING)
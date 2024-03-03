from threading import Thread

from dataaccess.utility import mongodb
from globals import to_dict
from models.Event import Event

collection: str = 'Event'
eventCache = {}


def GetEvent(eventId):
  if eventId in eventCache:
    return eventCache[eventId]
  e = mongodb.GetSingleDoc(collection, {'EventId': eventId})
  event = Event(e) if e else None
  if event:
    eventCache[eventId] = event
  return event


def GetAllEvents():
  eventList: list[Event] = []
  events = mongodb.GetManyDocs(collection, {})
  for e in events if events else []:
    if e:
      event = Event(e)
      eventCache[e.EventId] = event
      eventList.append(event)
  return eventList


def UpsertEvent(event: Event):
  eventCache[event.EventId] = event
  thread = Thread(target=PushEventToMongo, args=(event, ))
  thread.start()
  return event


def DeleteEvent(eventId):
  del eventCache[eventId]
  thread = Thread(target=DeleteEventFromMongo, args=(eventId, ))
  thread.start()
  return True


def PushEventToMongo(event: Event):
  mongodb.UpsertSingleDoc(collection, {'EventId': event.EventId},
                          to_dict(event))
  return


def DeleteEventFromMongo(eventId):
  mongodb.DeleteDocs(collection, {'EventId': eventId})
  return

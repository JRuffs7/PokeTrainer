from models.Event import Event


class Server:
  ServerName: str
  ServerId: int
  ChannelId: int
  CurrentEvent: Event|None

  def __init__(self, dict):
    vars(self).update(dict)
    self.CurrentEvent = Event(self.CurrentEvent) if self.CurrentEvent else None

class Server:
  ServerName: str
  ServerId: int
  ChannelId: int
  CurrentEventId: str | None

  def __init__(self, dict):
    vars(self).update(dict)

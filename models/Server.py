from typing import Dict, List

from models.Pokemon import Pokemon


class Server:
  ServerId: int
  ChannelIds: List[int]
  ServerName: str
  SpawnChance: int
  LastSpawned: Pokemon | None
  LastSpawnMessage: int
  LastSpawnChannel: int
  DeletePrevious: int
  CaughtBy: int
  FoughtBy: List[int]

  def __init__(self, dict: Dict | None):
    self.ServerId = dict.get('ServerId') or 0 if dict else 0
    channels = dict.get('ChannelIds') if dict else None
    self.ChannelIds = channels or [] if isinstance(
        channels, List) else channels.value if channels else []
    self.ServerName = dict.get('ServerName') or '' if dict else ''
    self.SpawnChance = dict.get('SpawnChance') or 0 if dict else 0
    spawned = dict.get('LastSpawned') if dict else None
    self.LastSpawned = Pokemon(spawned) or None if isinstance(
        spawned, Dict) else Pokemon(spawned.value) if spawned else None
    self.LastSpawnMessage = dict.get('LastSpawnMessage') or 0 if dict else 0
    self.LastSpawnChannel = dict.get('LastSpawnChannel') or 0 if dict else 0
    self.DeletePrevious = dict.get('DeletePrevious') if (dict and dict.get('DeletePrevious') is not None) else 1
    self.CaughtBy = dict.get('CaughtBy') or 0 if dict else 0
    fought = dict.get('FoughtBy') if dict else None
    self.FoughtBy = fought or [] if isinstance(
        fought, List) else fought.value if fought else []

  def __str__(self):
    return f"Server Name: {self.ServerName}\nSpawn Channels: {', '.join(f'<#{id}>' for id in self.ChannelIds)}\nSpawn Interval Chance: {self.SpawnChance}%\nDelete Prev. Spawn: {'Yes' if self.DeletePrevious else 'No'}"

"""
Generuje domyślny plik konfiguracji station.json.
Edytuj go ręcznie lub z poziomu przyszłego GUI.
"""

from core import StationConfig

cfg = StationConfig()
cfg.save("station.json")
print("Zapisano: station.json")

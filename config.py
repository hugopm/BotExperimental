import json
import os
import tempfile
from pathlib import Path
from threading import RLock

KEY_DESCRIPTIONS = {
    "CHANNEL_DEBRIEF": "ID du salon Discord #debrief-epreuve",
    "CHANNEL_RANKING": "ID du salon Discord #classement",
    "MESSAGE_CONFIRMATION": "Message affiché dans la commande de débrief. {user_mention} est automatiquement remplacé.",
    "NB_PROBLEMS": "Nombre de problèmes de l'épreuve.",
    "NOM_EPREUVE": "L'en-tête du classement sera \"Classement {NOM_EPREUVE}\".",
    "GUILD_ID": "ID du serveur Discord cible.",
    "LOCK_MSG": "Si ce message n'est pas vide, le salon #debrief-epreuve sera bloqué et ce message s'affichera lors de la commande /debrief. Utile pour bloquer le salon au FARIO.",
    "ROLE_DEBRIEF": "ID du rôle @debrief-epreuve.",
    "ROLE_FINALE": "ID du rôle des finalistes.",
    "ROLE_PARTICIPANT": "ID du rôle @participant-selection.",
    "ROLE_RANKING": "ID du rôle @score-publié.",
}


class ConfigStore:
    def __init__(self, file_path: Path):
        object.__setattr__(self, "_lock", RLock())
        object.__setattr__(self, "_file_path", file_path)
        object.__setattr__(self, "_data", self._load())

    def _load(self) -> dict:
        if not self._file_path.exists():
            raise FileNotFoundError(f"Missing config file: {self._file_path}")
        with self._file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"Invalid config format in {self._file_path}")
        return data

    def _atomic_write(self, data: dict):
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self._file_path.parent,
            delete=False,
        ) as tmp:
            tmp.write(serialized)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)

        os.replace(tmp_path, self._file_path)

    def __getattr__(self, key: str):
        with self._lock:
            if key == "ABC":
                nb = self._data["NB_PROBLEMS"]
                if not isinstance(nb, int) or nb <= 0:
                    raise ValueError("NB_PROBLEMS must be a positive integer.")
                return "+".join(chr(ord("A") + i) for i in range(nb))
            if key == "EXEMPLE":
                nb = self._data["NB_PROBLEMS"]
                if not isinstance(nb, int) or nb <= 0:
                    raise ValueError("NB_PROBLEMS must be a positive integer.")
                return "+".join(str(max(0, 100 - 10 * i)) for i in range(nb))
            if key not in self._data:
                raise AttributeError(f"Missing config key: {key}")
            return self._data[key]

    def __setattr__(self, key: str, value):
        if key.startswith("_"):
            object.__setattr__(self, key, value)
            return
        raise AttributeError("Config is read-only via attributes. Use save_all(dict).")

    def as_dict(self) -> dict:
        with self._lock:
            return dict(self._data)

    def descriptions(self) -> dict:
        return dict(KEY_DESCRIPTIONS)

    def save_all(self, data: dict):
        if not isinstance(data, dict):
            raise ValueError("Config payload must be a dict.")

        expected = set(self._data.keys())
        provided = set(data.keys())
        missing = expected - provided
        extra = provided - expected
        if missing:
            raise KeyError(f"Missing keys in payload: {sorted(missing)}")
        if extra:
            raise KeyError(f"Unknown keys in payload: {sorted(extra)}")

        with self._lock:
            self._data = dict(data)
            self._atomic_write(self._data)


cfg = ConfigStore(Path(__file__).with_name("config.json"))

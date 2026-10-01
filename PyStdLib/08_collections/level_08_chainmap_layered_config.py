"""
LEVEL 08 (advanced) - Interop: ChainMap + os.environ for layered configuration
==================================================================================
You will learn
  * ChainMap views multiple mappings as ONE, checking them in order without copying
  * a realistic layering: defaults < config file < environment overrides
  * writes through a ChainMap always land in the FIRST mapping, never the others

Run: python level_08_chainmap_layered_config.py
"""
import os
from collections import ChainMap

DEFAULTS = {"timeout": 30, "retries": 3, "host": "localhost"}
FILE_CONFIG = {"host": "config-file-host", "retries": 5}

if __name__ == "__main__":
    # simulate an environment override, scoped to this process only
    os.environ["APP_HOST"] = "env-override-host"
    env_overrides = {"host": os.environ["APP_HOST"]}

    # ChainMap checks mappings LEFT TO RIGHT: env overrides win over file config,
    # which wins over defaults -- and nothing is copied, it's a live view.
    config = ChainMap(env_overrides, FILE_CONFIG, DEFAULTS)

    assert config["host"] == "env-override-host"   # found in the first mapping
    assert config["retries"] == 5                   # not in env_overrides -> falls through to FILE_CONFIG
    assert config["timeout"] == 30                  # only in DEFAULTS -> falls through to the last one

    # the underlying mappings are untouched -- ChainMap is just a view over them
    assert FILE_CONFIG["host"] == "config-file-host"
    assert config.maps == [env_overrides, FILE_CONFIG, DEFAULTS]

    # ---- writes ALWAYS go to the first mapping, regardless of where the key lives ----
    config["retries"] = 10
    assert env_overrides["retries"] == 10   # written into the FIRST map...
    assert FILE_CONFIG["retries"] == 5      # ...the deeper one is untouched
    assert config["retries"] == 10          # reads see the new value (first map wins)

    # ---- new_child(): push a fresh layer on top without touching the rest --
    request_scope = config.new_child({"timeout": 5})   # e.g. a per-request timeout override
    assert request_scope["timeout"] == 5     # the new layer wins
    assert request_scope["host"] == "env-override-host"   # falls through for keys it doesn't have
    assert config["timeout"] == 30           # the original chain is unaffected

    del os.environ["APP_HOST"]   # clean up after ourselves
    print("OK")

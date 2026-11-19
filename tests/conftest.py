# -*- coding: utf-8 -*-
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path[:0] = [os.path.join(ROOT, "plugin.video.stvr"), os.path.join(ROOT, "dev", "stubs")]

# Profil doplnku (cache, Pozrieť neskôr) do dočasného adresára, nie do dev/profile.
os.environ["STVR_PROFILE"] = tempfile.mkdtemp(prefix="stvr-test-")

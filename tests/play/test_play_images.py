"""tools/play_publish.py: the images of a listing are replaced only when they changed (Google's answers simulated)."""
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
pytest.importorskip("google.auth")
import play_publish as pp  # noqa: E402


class Resp:
    def __init__(self, data=None):
        self.status_code, self._data, self.content, self.text, self.request = 200, data or {}, b"x", "", None

    def json(self):
        return self._data


class Play:
    """A listing image store as Play keeps it: each image with its sha256."""
    def __init__(self, images):
        self.images, self.calls = list(images), []

    def get(self, url, **kw):
        return Resp({"images": [{"sha256": h} for h in self.images]})

    def delete(self, url, **kw):
        self.calls.append("delete")
        self.images = []
        return Resp()

    def post(self, url, data=None, **kw):
        self.calls.append("upload")
        self.images.append(hashlib.sha256(data.read()).hexdigest())
        return Resp()


def test_images_are_replaced_only_when_they_changed(tmp_path):
    files = []
    for i, body in enumerate((b"one", b"two")):
        f = tmp_path / f"{i}.png"
        f.write_bytes(body)
        files.append(f)
    s = Play([])
    assert pp.replace_images(s, "e", "en-US", "phoneScreenshots", files) is True
    assert s.calls == ["upload", "upload"]                                   # nothing to delete at first
    s.calls.clear()
    assert pp.replace_images(s, "e", "en-US", "phoneScreenshots", files) is False
    assert s.calls == []                                                     # the same: left as they are
    assert pp.replace_images(s, "e", "en-US", "phoneScreenshots", files[::-1]) is True
    assert s.calls == ["delete", "upload", "upload"]                         # another order is a change

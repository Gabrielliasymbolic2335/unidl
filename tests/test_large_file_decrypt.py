from __future__ import annotations

import mmap

from unidl.downloader import cenc_fragment


def test_large_fragment_decryption_uses_a_disk_mapping(tmp_path, monkeypatch):
    source = tmp_path / "source.mp4"
    output = tmp_path / "clear.mp4"
    source.write_bytes(b"\x00" * (1024 * 1024))
    monkeypatch.setattr(cenc_fragment, "MMAP_DECRYPT_THRESHOLD", 1)

    seen: dict[str, bool] = {}

    def inspect(data, *_args, **_kwargs):
        seen["mapped"] = isinstance(data, mmap.mmap)
        return None

    monkeypatch.setattr(cenc_fragment, "_decrypt_cenc_fragment_buffer", inspect)

    assert cenc_fragment.decrypt_cenc_fragment(source, [], output) is None
    assert seen == {"mapped": True}
    assert not output.exists()
    assert not list(tmp_path.glob(".*.tmp"))


def test_large_fragment_decryption_replaces_output_atomically(tmp_path, monkeypatch):
    source = tmp_path / "source.mp4"
    output = tmp_path / "clear.mp4"
    source.write_bytes(b"encrypted")
    monkeypatch.setattr(cenc_fragment, "MMAP_DECRYPT_THRESHOLD", 1)

    def decrypt(data, *_args, **_kwargs):
        data[0] = ord("c")
        return object()

    monkeypatch.setattr(cenc_fragment, "_decrypt_cenc_fragment_buffer", decrypt)

    assert cenc_fragment.decrypt_cenc_fragment(source, [], output) == output
    assert output.read_bytes() == b"cncrypted"
    assert source.read_bytes() == b"encrypted"
    assert not list(tmp_path.glob(".*.tmp"))

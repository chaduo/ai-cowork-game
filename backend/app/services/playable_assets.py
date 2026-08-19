from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Literal

from dulwich.errors import NotGitRepository

from app.models import PlayableVersion
from app.services.project_git import ProjectGitService


IMAGE_MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
}
AUDIO_MIME_TYPES = {
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".flac": "audio/flac",
}
FONT_MIME_TYPES = {
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
}


@dataclass(frozen=True)
class PlayableAsset:
    path: str
    name: str
    kind: Literal["image", "audio", "font"]
    mime_type: str
    size_bytes: int


class PlayableAssetService:
    def __init__(self, git: ProjectGitService) -> None:
        self._git = git

    def list_assets(self, version: PlayableVersion) -> list[PlayableAsset]:
        if not version.git_commit:
            raise ValueError("playable version has no immutable checkpoint")
        try:
            entries = self._git.list_files(version.project_id, version.git_commit, prefix="playable/")
        except (KeyError, NotGitRepository) as cause:
            raise ValueError("playable checkpoint is unavailable") from cause
        assets: list[PlayableAsset] = []
        for entry in entries:
            relative_path = entry.path.removeprefix("playable/")
            asset = self._asset(relative_path, entry.size_bytes)
            if asset is not None:
                assets.append(asset)
        return assets

    def read_asset(self, version: PlayableVersion, relative_path: str) -> tuple[PlayableAsset, bytes]:
        path = self._normalize_asset_path(relative_path)
        asset = self._asset(path, 0)
        if asset is None:
            raise ValueError("unsupported playable asset")
        if not version.git_commit:
            raise ValueError("playable version has no immutable checkpoint")
        try:
            content = self._git.read_file(version.project_id, version.git_commit, f"playable/{path}")
        except (KeyError, NotGitRepository) as cause:
            raise ValueError("playable asset not found") from cause
        return self._asset(path, len(content)) or asset, content

    @staticmethod
    def _normalize_asset_path(value: str) -> str:
        if not value or value.startswith(("/", "~")) or "\\" in value or "://" in value or "\x00" in value:
            raise ValueError("invalid playable asset path")
        parts = value.split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise ValueError("invalid playable asset path")
        return "/".join(parts)

    @staticmethod
    def _asset(path: str, size_bytes: int) -> PlayableAsset | None:
        suffix = PurePosixPath(path).suffix.lower()
        if suffix in IMAGE_MIME_TYPES:
            kind: Literal["image", "audio", "font"] = "image"
            mime_type = IMAGE_MIME_TYPES[suffix]
        elif suffix in AUDIO_MIME_TYPES:
            kind = "audio"
            mime_type = AUDIO_MIME_TYPES[suffix]
        elif suffix in FONT_MIME_TYPES:
            kind = "font"
            mime_type = FONT_MIME_TYPES[suffix]
        else:
            return None
        return PlayableAsset(
            path=path,
            name=PurePosixPath(path).name,
            kind=kind,
            mime_type=mime_type,
            size_bytes=size_bytes,
        )

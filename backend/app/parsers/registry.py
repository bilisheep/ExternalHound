"""
Parser registry and plugin discovery.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable

import tomllib

from app.config import BASE_DIR
from app.parsers.base import BaseParser, PluginManifest

logger = logging.getLogger(__name__)

DEFAULT_PLUGIN_DIR = BASE_DIR.parent / "plugins"


class ParserRegistry:
    """Registry for parser plugins."""

    def __init__(self) -> None:
        self._parsers: dict[str, type[BaseParser]] = {}
        self._manifests: dict[str, PluginManifest] = {}

    @property
    def manifests(self) -> list[PluginManifest]:
        return list(self._manifests.values())

    def register(self, manifest: PluginManifest, parser_cls: type[BaseParser]) -> None:
        if not issubclass(parser_cls, BaseParser):
            raise TypeError("Parser class must inherit from BaseParser")
        parser_cls.manifest = manifest
        self._parsers[manifest.name] = parser_cls
        self._manifests[manifest.name] = manifest
        logger.info("Registered parser plugin: %s", manifest.name)

    def get(self, name: str) -> type[BaseParser] | None:
        return self._parsers.get(name)

    def discover(self, plugin_dirs: Iterable[Path] | None = None) -> list[PluginManifest]:
        roots = list(plugin_dirs) if plugin_dirs else [DEFAULT_PLUGIN_DIR]
        for root in roots:
            self._discover_in_root(Path(root))
        return self.manifests

    def select_parser(
        self,
        file_path: Path,
        parser_name: str | None = None,
    ) -> type[BaseParser]:
        if parser_name:
            parser = self.get(parser_name)
            if not parser:
                raise ValueError(f"Parser not found: {parser_name}")
            return parser
        for parser_cls in self._sorted_parsers():
            if parser_cls.probe(file_path):
                return parser_cls
        raise ValueError(f"No parser matched input: {file_path}")

    def _sorted_parsers(self) -> list[type[BaseParser]]:
        def _priority(item: type[BaseParser]) -> int:
            manifest = item.manifest
            return manifest.priority if manifest else 100

        return sorted(self._parsers.values(), key=_priority)

    def _discover_in_root(self, root: Path) -> None:
        if not root.exists():
            logger.debug("Plugin root not found: %s", root)
            return
        for plugin_dir in root.iterdir():
            if not plugin_dir.is_dir():
                continue
            manifest_path = plugin_dir / "plugin.toml"
            if not manifest_path.is_file():
                continue
            try:
                manifest = self._load_manifest(manifest_path)
                parser_cls = self._load_entrypoint(manifest, plugin_dir)
                self.register(manifest, parser_cls)
            except Exception as exc:
                logger.error(
                    "Failed to load plugin from %s: %s",
                    plugin_dir,
                    exc,
                )

    def _load_manifest(self, manifest_path: Path) -> PluginManifest:
        with manifest_path.open("rb") as handle:
            data = tomllib.load(handle)
        plugin_data = data.get("plugin") if isinstance(data, dict) else None
        if isinstance(plugin_data, dict):
            data = plugin_data
        if not isinstance(data, dict):
            raise ValueError(f"Invalid manifest: {manifest_path}")
        return PluginManifest.from_mapping(data, manifest_path)

    def _load_entrypoint(
        self,
        manifest: PluginManifest,
        plugin_dir: Path,
    ) -> type[BaseParser]:
        module_part, _, attr = manifest.entrypoint.partition(":")
        if not module_part or not attr:
            raise ValueError(
                f"Invalid entrypoint for {manifest.name}: {manifest.entrypoint}"
            )
        module_path = self._resolve_module_path(plugin_dir, module_part)
        module = self._load_module(manifest.name, module_path)
        parser_cls = getattr(module, attr, None)
        if parser_cls is None:
            raise ValueError(
                f"Entrypoint not found: {manifest.entrypoint} in {module_path}"
            )
        if not issubclass(parser_cls, BaseParser):
            raise TypeError(
                f"Entrypoint {manifest.entrypoint} does not inherit BaseParser"
            )
        return parser_cls

    def _resolve_module_path(self, plugin_dir: Path, module_part: str) -> Path:
        module_part = module_part.strip()
        if module_part.endswith(".py"):
            return plugin_dir / module_part
        module_file = module_part.replace(".", "/") + ".py"
        return plugin_dir / module_file

    def _load_module(self, plugin_name: str, module_path: Path) -> ModuleType:
        if not module_path.is_file():
            raise FileNotFoundError(f"Plugin module not found: {module_path}")
        module_name = f"externalhound_plugin_{plugin_name}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module: {module_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        self._ensure_backend_on_path()
        spec.loader.exec_module(module)
        return module

    def _ensure_backend_on_path(self) -> None:
        backend_path = str(BASE_DIR)
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)


default_registry = ParserRegistry()

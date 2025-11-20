"""
Persistence-Service - Speichert/lädt Projekte, Config, Snapshots
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from models.project import Project

logger = logging.getLogger(__name__)


class PersistenceService:
    """
    Verwaltet alle persistierten Daten im Benutzerverzeichnis

    Struktur:
    - Windows: %APPDATA%/abc_co2_bilanzierer/
    - macOS/Linux: ~/.abc_co2_bilanzierer/

    Dateien:
    - config.json (zuletzt geöffnete Projekte, CSV-Pfad, UI-Einstellungen)
    - projects/<project_id>.json (komplettes Projekt)
    - snapshots/<project_id>/<timestamp>.json (Autosave-Verläufe, max. 20)
    """

    MAX_SNAPSHOTS = 20

    def __init__(self, base_dir: Optional[str] = None):
        """
        Args:
            base_dir: Optional benutzerdefiniertes Verzeichnis
        """
        if base_dir:
            self.base_path = Path(base_dir)
        else:
            # Automatische Erkennung
            home = Path.home()
            self.base_path = home / '.abc_co2_bilanzierer'

        self.projects_path = self.base_path / 'projects'
        self.snapshots_path = self.base_path / 'snapshots'
        self.logs_path = self.base_path / 'logs'
        self.config_file = self.base_path / 'config.json'

        self.logger = logger

        # Verzeichnisse erstellen
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Erstellt alle benötigten Verzeichnisse"""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.projects_path.mkdir(exist_ok=True)
            self.snapshots_path.mkdir(exist_ok=True)
            self.logs_path.mkdir(exist_ok=True)
            self.logger.info(f"Verzeichnisse erstellt: {self.base_path}")
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der Verzeichnisse: {e}")

    def _sanitize_filename(self, name: str, project_id: str) -> str:
        """
        Macht Projektnamen dateisystem-sicher

        Args:
            name: Projektname
            project_id: Projekt-ID als Fallback

        Returns:
            Sicherer Dateiname
        """
        import re

        # Sonderzeichen entfernen/ersetzen
        safe_name = name.strip()
        # Windows-Sonderzeichen
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', safe_name)
        safe_name = safe_name.replace(' ', '_')

        # Max. 100 Zeichen
        if len(safe_name) > 100:
            safe_name = safe_name[:100]

        # Falls leer: ID verwenden
        if not safe_name:
            safe_name = f"projekt_{project_id[:8]}"

        return safe_name

    def _get_unique_filename(self, base_name: str, extension: str = ".json") -> Path:
        """
        Findet einen eindeutigen Dateinamen bei Konflikten

        Args:
            base_name: Basis-Dateiname
            extension: Datei-Endung

        Returns:
            Eindeutiger Dateipfad
        """
        filepath = self.projects_path / f"{base_name}{extension}"

        # Wenn keine Kollision, direkt zurückgeben
        if not filepath.exists():
            return filepath

        # Bei Kollision: Nummer anhängen
        counter = 1
        while True:
            filepath = self.projects_path / f"{base_name}_{counter}{extension}"
            if not filepath.exists():
                return filepath
            counter += 1

    def save_project(self, project: Project, custom_path: Optional[str] = None) -> bool:
        """
        Speichert Projekt als JSON

        Args:
            project: Zu speicherndes Projekt
            custom_path: Optionaler benutzerdefinierter Pfad für "Speichern unter"

        Returns:
            True bei Erfolg
        """
        try:
            if custom_path:
                # Benutzerdefinierter Pfad (Speichern unter)
                project_file = Path(custom_path)

                # Speichere externen Pfad in config.json
                self._register_external_project(project.id, str(project_file))
            else:
                # Prüfe ob Projekt bereits als extern registriert ist
                config = self.load_config()
                external_paths = config.get('external_project_paths', {})

                if project.id in external_paths:
                    # Projekt ist extern → Speichere an externem Pfad
                    external_file = Path(external_paths[project.id])
                    if external_file.exists() or external_file.parent.exists():
                        project_file = external_file
                    else:
                        # Externer Pfad existiert nicht mehr → Fallback zu Standard
                        filename = self._sanitize_filename(
                            project.name, project.id)
                        project_file = self._get_unique_filename(filename)
                else:
                    # Standard: Projektname.json (ohne UUID)
                    filename = self._sanitize_filename(
                        project.name, project.id)

                    # Migration: Alte Datei mit UUID finden und löschen
                    old_filename_with_uuid = filename + f"_{project.id[:8]}"
                    old_file_with_uuid = self.projects_path / \
                        f"{old_filename_with_uuid}.json"

                    if old_file_with_uuid.exists():
                        # Alte Datei gefunden - migrieren
                        project_file = self.projects_path / f"{filename}.json"
                        # Alte Datei wird später gelöscht, nachdem neue gespeichert wurde
                    else:
                        # Keine Migration nötig - normale Logik
                        project_file = self._get_unique_filename(filename)

                    # Speichere Pfad im Projekt für spätere Nutzung
                    project.file_path = str(project_file)

            # Zeitstempel aktualisieren
            project.update_timestamp()

            # Als JSON speichern
            data = project.to_dict()
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Migration: Alte Datei mit UUID löschen (falls vorhanden)
            if not custom_path and project.id not in external_paths:
                filename = self._sanitize_filename(project.name, project.id)
                old_filename_with_uuid = filename + f"_{project.id[:8]}"
                old_file_with_uuid = self.projects_path / \
                    f"{old_filename_with_uuid}.json"

                if old_file_with_uuid.exists() and old_file_with_uuid != project_file:
                    old_file_with_uuid.unlink()
                    self.logger.info(
                        f"Alte Projektdatei migriert: {old_file_with_uuid.name} → {project_file.name}")

            self.logger.info(
                f"Projekt gespeichert: {project.name} → {project_file.name}")
            return True

        except Exception as e:
            self.logger.error(
                f"Fehler beim Speichern von Projekt {project.id}: {e}",
                exc_info=True
            )
            return False

    def load_project(self, project_id: str) -> Optional[Project]:
        """
        Lädt Projekt aus JSON (sucht in Standard-Ordner und externen Pfaden)

        Args:
            project_id: ID des zu ladenden Projekts

        Returns:
            Project-Objekt oder None
        """
        try:
            # Zuerst: Versuche direkte ID-Datei (alte Variante)
            project_file = self.projects_path / f"{project_id}.json"

            # Falls nicht gefunden: Suche nach Datei mit ID im Namen
            if not project_file.exists():
                # Suche nach Datei, die die ID enthält (z.B. Projektname_ID.json)
                # ID kann verkürzt sein (erste 8 Zeichen)
                short_id = project_id[:8]

                for candidate in self.projects_path.glob("*.json"):
                    # Prüfe ob Dateiname die ID enthält
                    if short_id in candidate.stem or project_id in candidate.stem:
                        # Prüfe ob die ID im JSON übereinstimmt
                        try:
                            with open(candidate, 'r', encoding='utf-8') as f:
                                data = json.load(f)

                            if data.get('id') == project_id:
                                project_file = candidate
                                break
                        except Exception:
                            continue

            # Falls immer noch nicht gefunden: Prüfe externe Pfade
            if not project_file.exists():
                config = self.load_config()
                external_paths = config.get('external_project_paths', {})

                if project_id in external_paths:
                    external_file = Path(external_paths[project_id])
                    if external_file.exists():
                        project_file = external_file

            if not project_file.exists():
                self.logger.warning(f"Projekt nicht gefunden: {project_id}")
                return None

            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            project = Project.from_dict(data)
            self.logger.info(f"Projekt geladen: {project.name} ({project.id})")

            # Prüfe auf neueren Snapshot
            restored = self._try_restore_snapshot(project)
            if restored:
                return restored

            return project

        except Exception as e:
            self.logger.error(
                f"Fehler beim Laden von Projekt {project_id}: {e}",
                exc_info=True
            )
            return None

    def save_snapshot(self, project: Project) -> bool:
        """
        Speichert Autosave-Snapshot

        Args:
            project: Zu speicherndes Projekt

        Returns:
            True bei Erfolg
        """
        try:
            # Snapshot-Verzeichnis für Projekt
            snapshot_dir = self.snapshots_path / project.id
            snapshot_dir.mkdir(exist_ok=True)

            # Timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_file = snapshot_dir / f"autosave_{timestamp}.json"

            # Speichern
            data = project.to_dict()
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Alte Snapshots löschen (max. 20 behalten)
            self._cleanup_old_snapshots(project.id)

            self.logger.debug(f"Snapshot gespeichert: {snapshot_file.name}")
            return True

        except Exception as e:
            self.logger.error(
                f"Fehler beim Speichern von Snapshot: {e}",
                exc_info=True
            )
            return False

    def _cleanup_old_snapshots(self, project_id: str) -> None:
        """
        Löscht älteste Snapshots (max. 20 behalten)

        Args:
            project_id: Projekt-ID
        """
        try:
            snapshot_dir = self.snapshots_path / project_id
            if not snapshot_dir.exists():
                return

            # Alle Snapshots sammeln
            snapshots = sorted(
                snapshot_dir.glob("autosave_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            # Älteste löschen
            for snapshot in snapshots[self.MAX_SNAPSHOTS:]:
                snapshot.unlink()
                self.logger.debug(f"Alter Snapshot gelöscht: {snapshot.name}")

        except Exception as e:
            self.logger.warning(f"Fehler beim Löschen alter Snapshots: {e}")

    def _try_restore_snapshot(self, project: Project) -> Optional[Project]:
        """
        Versucht neuesten Snapshot zu laden, falls neuer als Projekt

        Args:
            project: Geladenes Projekt

        Returns:
            Wiederhergestelltes Projekt oder None
        """
        try:
            snapshot_dir = self.snapshots_path / project.id
            if not snapshot_dir.exists():
                return None

            # Neuester Snapshot
            snapshots = sorted(
                snapshot_dir.glob("autosave_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            if not snapshots:
                return None

            newest_snapshot = snapshots[0]

            # Zeitstempel vergleichen
            project_time = datetime.fromisoformat(project.updated_at)
            snapshot_time = datetime.fromtimestamp(
                newest_snapshot.stat().st_mtime)

            if snapshot_time > project_time:
                self.logger.info(
                    f"Neuerer Snapshot gefunden, stelle wieder her: "
                    f"{newest_snapshot.name}"
                )

                with open(newest_snapshot, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                return Project.from_dict(data)

            return None

        except Exception as e:
            self.logger.warning(f"Fehler beim Snapshot-Restore: {e}")
            return None

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        Listet alle vorhandenen Projekte auf (inkl. externe Pfade)
        Sortiert nach recent_projects Liste aus config.json

        Returns:
            Liste mit Projekt-Metadaten (id, name, updated_at), sortiert nach Nutzung
        """
        projects = []
        seen_ids = set()
        projects_by_id = {}  # Zum schnellen Lookup

        try:
            # 1. Projekte im Standard-Ordner
            for project_file in self.projects_path.glob("*.json"):
                try:
                    with open(project_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    project_id = data.get('id', '')
                    if project_id:
                        seen_ids.add(project_id)

                    project_data = {
                        'id': project_id,
                        'name': data.get('name', 'Unbenannt'),
                        'updated_at': data.get('updated_at', ''),
                        'created_at': data.get('created_at', '')
                    }
                    projects.append(project_data)
                    if project_id:
                        projects_by_id[project_id] = project_data
                except Exception as e:
                    self.logger.warning(
                        f"Fehler beim Lesen von {project_file.name}: {e}"
                    )

            # 2. Extern gespeicherte Projekte aus config.json
            config = self.load_config()
            external_paths = config.get('external_project_paths', {})
            updated_external_paths = {}

            for project_id, filepath in external_paths.items():
                # Überspringe bereits geladene IDs (aus projects-Ordner)
                if project_id in seen_ids:
                    # Prüfe ob externe Datei noch existiert, wenn nicht: aus config entfernen
                    if Path(filepath).exists():
                        updated_external_paths[project_id] = filepath
                    continue

                try:
                    project_file = Path(filepath)

                    # Falls Datei nicht existiert: Suche nach umbenannter/verschobener Datei mit gleicher UUID
                    if not project_file.exists():
                        # Suche im gleichen Verzeichnis nach JSON-Dateien mit dieser UUID
                        parent_dir = project_file.parent
                        if parent_dir.exists():
                            for candidate in parent_dir.glob("*.json"):
                                try:
                                    with open(candidate, 'r', encoding='utf-8') as f:
                                        data = json.load(f)
                                    if data.get('id') == project_id:
                                        # Gefunden! Aktualisiere Pfad
                                        project_file = candidate
                                        updated_external_paths[project_id] = str(
                                            candidate)
                                        self.logger.info(
                                            f"Externe Projektdatei gefunden (umbenannt): {candidate.name}")
                                        break
                                except Exception:
                                    continue

                        # Immer noch nicht gefunden? Überspringe
                        if not project_file.exists():
                            self.logger.warning(
                                f"Externe Projektdatei nicht mehr vorhanden: {filepath}")
                            continue
                    else:
                        updated_external_paths[project_id] = filepath

                    with open(project_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    project_data = {
                        'id': data.get('id', ''),
                        'name': data.get('name', 'Unbenannt'),
                        'updated_at': data.get('updated_at', ''),
                        'created_at': data.get('created_at', ''),
                        'external': True  # Markiere als extern
                    }
                    projects.append(project_data)
                    projects_by_id[project_id] = project_data
                except Exception as e:
                    self.logger.warning(
                        f"Fehler beim Lesen von externem Projekt {filepath}: {e}"
                    )

            # Speichere aktualisierte externe Pfade (falls welche umbenannt wurden)
            if updated_external_paths != external_paths:
                config['external_project_paths'] = updated_external_paths
                self.save_config(config)
                self.logger.info("Externe Projekt-Pfade aktualisiert")

            # 3. Sortiere nach recent_projects Liste
            recent_ids = config.get('recent_projects', [])

            # Säubere recent_ids: Nur gültige Projekt-IDs behalten (die tatsächlich existieren)
            valid_recent_ids = [
                pid for pid in recent_ids if pid in projects_by_id]

            # Falls ungültige Einträge entfernt wurden, speichere bereinigte Liste
            if len(valid_recent_ids) != len(recent_ids):
                config['recent_projects'] = valid_recent_ids
                self.save_config(config)
                self.logger.info(
                    f"Recent Projects bereinigt: {len(recent_ids) - len(valid_recent_ids)} ungültige Einträge entfernt")

            if valid_recent_ids:
                # Erstelle sortierte Liste: erst recent, dann restliche
                sorted_projects = []

                # Zuerst: Projekte aus recent_projects (in dieser Reihenfolge)
                for project_id in valid_recent_ids:
                    if project_id in projects_by_id:
                        sorted_projects.append(projects_by_id[project_id])

                # Dann: Restliche Projekte (nach Datum sortiert)
                remaining = [p for p in projects if p['id']
                             not in valid_recent_ids]

                remaining.sort(
                    key=lambda p: p.get('updated_at', ''),
                    reverse=True
                )
                sorted_projects.extend(remaining)

                projects = sorted_projects
            else:
                # Fallback: Nach Datum sortieren
                projects.sort(
                    key=lambda p: p.get('updated_at', ''),
                    reverse=True
                )

        except Exception as e:
            self.logger.error(f"Fehler beim Listen der Projekte: {e}")

        return projects

    def rename_project_file(self, project: Project, old_name: str) -> bool:
        """
        Benennt die JSON-Datei eines Projekts um, wenn der Projektname geändert wurde.

        Args:
            project: Projekt mit neuem Namen
            old_name: Alter Projektname

        Returns:
            True bei Erfolg
        """
        try:
            # Prüfe ob Projekt extern gespeichert ist
            config = self.load_config()
            external_paths = config.get('external_project_paths', {})

            if project.id in external_paths:
                # Externe Projekte: Prüfe ob Datei existiert und umbenennen
                external_file = Path(external_paths[project.id])
                if not external_file.exists():
                    self.logger.warning(
                        f"Externe Projektdatei nicht gefunden: {external_file}")
                    return False

                # Neuer Dateiname im gleichen Verzeichnis
                new_filename = self._sanitize_filename(
                    project.name, project.id)
                new_file = external_file.parent / f"{new_filename}.json"

                # Umbenennen wenn unterschiedlich
                if external_file != new_file:
                    external_file.rename(new_file)
                    # Externen Pfad in config aktualisieren
                    self._register_external_project(project.id, str(new_file))
                    self.logger.info(
                        f"✓ Externes Projekt umbenannt: {external_file.name} → {new_file.name}")
                return True

            # Alte Datei finden (kann auch alte Variante mit UUID sein)
            old_filename_with_uuid = self._sanitize_filename(
                old_name, project.id) + f"_{project.id[:8]}"
            old_filename = self._sanitize_filename(old_name, project.id)

            self.logger.info(
                f"Umbenennung: Suche alte Datei für '{old_name}' → '{project.name}'")

            # Prüfe beide Varianten (mit und ohne UUID für Migration)
            old_file = None
            if (self.projects_path / f"{old_filename_with_uuid}.json").exists():
                old_file = self.projects_path / \
                    f"{old_filename_with_uuid}.json"
                self.logger.info(
                    f"Alte Datei gefunden (mit UUID): {old_file.name}")
            elif (self.projects_path / f"{old_filename}.json").exists():
                old_file = self.projects_path / f"{old_filename}.json"
                self.logger.info(
                    f"Alte Datei gefunden (ohne UUID): {old_file.name}")
            else:
                # Suche nach Projekt-ID in allen JSON-Dateien
                self.logger.info(
                    f"Suche Datei nach ID in {self.projects_path}")
                for json_file in self.projects_path.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if data.get('id') == project.id:
                                old_file = json_file
                                self.logger.info(
                                    f"Datei per ID gefunden: {old_file.name}")
                                break
                    except:
                        continue

            if not old_file or not old_file.exists():
                self.logger.warning(
                    f"Alte Projektdatei nicht gefunden für: {old_name} (ID: {project.id[:8]})")
                return False

            # Neue Datei erstellen
            new_filename = self._sanitize_filename(project.name, project.id)
            new_file = self._get_unique_filename(new_filename)

            # Umbenennen, falls sich der Name ändert
            if old_file != new_file:
                self.logger.info(f"Benenne um: {old_file} → {new_file}")
                old_file.rename(new_file)
                self.logger.info(
                    f"✓ Projektdatei umbenannt: {old_file.name} → {new_file.name}")
            else:
                self.logger.info("Keine Umbenennung nötig (gleicher Name)")

            return True

        except Exception as e:
            self.logger.error(
                f"Fehler beim Umbenennen der Projektdatei: {e}", exc_info=True)
            return False

    def delete_project(self, project_id: str) -> bool:
        """
        Löscht ein Projekt und seine Snapshots

        Args:
            project_id: ID des zu löschenden Projekts

        Returns:
            True bei Erfolg
        """
        try:
            # Projekt-Datei löschen
            project_file = self.projects_path / f"{project_id}.json"
            if project_file.exists():
                project_file.unlink()

            # Snapshot-Verzeichnis löschen
            snapshot_dir = self.snapshots_path / project_id
            if snapshot_dir.exists():
                for snapshot in snapshot_dir.glob("*.json"):
                    snapshot.unlink()
                snapshot_dir.rmdir()

            self.logger.info(f"Projekt gelöscht: {project_id}")
            return True

        except Exception as e:
            self.logger.error(
                f"Fehler beim Löschen von Projekt {project_id}: {e}")
            return False

    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Speichert Konfiguration (zuletzt geöffnete Projekte, CSV-Pfad, etc.)

        Args:
            config: Konfigurations-Dictionary

        Returns:
            True bei Erfolg
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.logger.debug("Konfiguration gespeichert")
            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Konfiguration: {e}")
            return False

    def load_config(self) -> Dict[str, Any]:
        """
        Lädt Konfiguration

        Returns:
            Konfigurations-Dictionary (oder leeres Dict)
        """
        try:
            if not self.config_file.exists():
                return {}

            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.logger.debug("Konfiguration geladen")
            return config

        except Exception as e:
            self.logger.warning(f"Fehler beim Laden der Konfiguration: {e}")
            return {}

    def _register_external_project(self, project_id: str, filepath: str) -> None:
        """Registriert externen Projekt-Pfad in config.json"""
        try:
            config = self.load_config()

            if 'external_project_paths' not in config:
                config['external_project_paths'] = {}

            config['external_project_paths'][project_id] = filepath
            self.save_config(config)

            self.logger.info(f"Externer Projekt-Pfad registriert: {filepath}")
        except Exception as e:
            self.logger.warning(
                f"Fehler beim Registrieren des externen Pfads: {e}")

    def get_log_path(self) -> Path:
        """Gibt Pfad zum Log-Verzeichnis zurück"""
        return self.logs_path

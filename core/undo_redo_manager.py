"""
Undo/Redo Manager für CO2-Bilanzierer

Verwaltet eine History von Project-States mit max. 10 Schritten.
"""

import logging
from typing import Optional, Any
import copy


class UndoRedoManager:
    """
    Generischer Undo/Redo Manager mit Stack-basierter Implementierung.
    
    Features:
    - Max. 10 Schritte History
    - Deep Copy von States
    - Redo-Stack wird bei neuer Änderung gelöscht
    - Thread-safe Design (für zukünftige Erweiterungen)
    """
    
    def __init__(self, max_history: int = 10):
        """
        Initialisiert den Undo/Redo Manager.
        
        Args:
            max_history: Maximale Anzahl von Undo-Schritten (Standard: 10)
        """
        self.max_history = max_history
        self.undo_stack: list[Any] = []
        self.redo_stack: list[Any] = []
        self.current_state: Optional[Any] = None
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"UndoRedoManager initialisiert (max_history={max_history})")
    
    def push_state(self, new_state: Any) -> None:
        """
        Speichert einen neuen State in der History.
        
        Wenn der aktuelle State existiert, wird er in den Undo-Stack verschoben.
        Der Redo-Stack wird komplett geleert (da neue Änderung durchgeführt wurde).
        
        Args:
            new_state: Der neue State (wird deep-copied)
        """
        # Aktuellen State in Undo-Stack verschieben (falls vorhanden)
        if self.current_state is not None:
            self.undo_stack.append(self.current_state)
            
            # Ältesten State entfernen, wenn Limit überschritten
            if len(self.undo_stack) > self.max_history:
                removed = self.undo_stack.pop(0)
                self.logger.debug("Ältester State aus History entfernt (Limit erreicht)")
        
        # Neuen State als current setzen (Deep Copy)
        self.current_state = self._deep_copy_state(new_state)
        
        # Redo-Stack leeren (neue Änderung verwirft Redo-History)
        if self.redo_stack:
            self.logger.debug(f"Redo-Stack geleert ({len(self.redo_stack)} Einträge)")
            self.redo_stack.clear()
        
        self.logger.debug(
            f"State gepusht (Undo: {len(self.undo_stack)}, Redo: {len(self.redo_stack)})"
        )
    
    def undo(self) -> Optional[Any]:
        """
        Macht die letzte Änderung rückgängig.
        
        Returns:
            Der vorherige State oder None wenn kein Undo möglich
        """
        if not self.can_undo():
            self.logger.debug("Undo nicht möglich (keine History)")
            return None
        
        # Current State in Redo-Stack verschieben
        if self.current_state is not None:
            self.redo_stack.append(self.current_state)
        
        # Vorherigen State aus Undo-Stack holen
        self.current_state = self.undo_stack.pop()
        
        self.logger.info(
            f"Undo durchgeführt (Undo: {len(self.undo_stack)}, Redo: {len(self.redo_stack)})"
        )
        
        # Deep Copy zurückgeben für Sicherheit
        return self._deep_copy_state(self.current_state)
    
    def redo(self) -> Optional[Any]:
        """
        Stellt eine rückgängig gemachte Änderung wieder her.
        
        Returns:
            Der nächste State oder None wenn kein Redo möglich
        """
        if not self.can_redo():
            self.logger.debug("Redo nicht möglich (keine Redo-History)")
            return None
        
        # Current State in Undo-Stack verschieben
        if self.current_state is not None:
            self.undo_stack.append(self.current_state)
        
        # Nächsten State aus Redo-Stack holen
        self.current_state = self.redo_stack.pop()
        
        self.logger.info(
            f"Redo durchgeführt (Undo: {len(self.undo_stack)}, Redo: {len(self.redo_stack)})"
        )
        
        # Deep Copy zurückgeben für Sicherheit
        return self._deep_copy_state(self.current_state)
    
    def can_undo(self) -> bool:
        """
        Prüft ob Undo möglich ist.
        
        Returns:
            True wenn mindestens ein Undo-Schritt verfügbar ist
        """
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """
        Prüft ob Redo möglich ist.
        
        Returns:
            True wenn mindestens ein Redo-Schritt verfügbar ist
        """
        return len(self.redo_stack) > 0
    
    def clear(self) -> None:
        """
        Löscht die komplette History (Undo + Redo).
        
        Nützlich beim Laden eines neuen Projekts.
        """
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.current_state = None
        self.logger.info("Undo/Redo History komplett gelöscht")
    
    def get_history_info(self) -> dict:
        """
        Gibt Debug-Informationen über den aktuellen Zustand zurück.
        
        Returns:
            Dictionary mit Undo/Redo Zählern
        """
        return {
            'undo_count': len(self.undo_stack),
            'redo_count': len(self.redo_stack),
            'can_undo': self.can_undo(),
            'can_redo': self.can_redo(),
            'has_current': self.current_state is not None
        }
    
    def _deep_copy_state(self, state: Any) -> Any:
        """
        Erstellt eine Deep Copy des States.
        
        Args:
            state: Der zu kopierende State
            
        Returns:
            Deep Copy des States
        """
        try:
            return copy.deepcopy(state)
        except Exception as e:
            self.logger.error(f"Fehler beim Deep Copy: {e}")
            # Fallback: Verwende den originalen State (nicht ideal aber besser als Crash)
            return state

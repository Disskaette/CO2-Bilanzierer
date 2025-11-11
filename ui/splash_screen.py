"""
Splash Screen - Ladefenster beim App-Start
"""

import customtkinter as ctk


class SplashScreen(ctk.CTkToplevel):
    """
    Splash Screen / Ladefenster

    Zeigt Logo, Versionsnummer und Ladefortschritt während der Initialisierung
    """

    def __init__(self, parent, version: str = "2.0"):
        super().__init__(parent)

        self.version = version

        # Fenster-Konfiguration
        self.title("")  # Kein Titel
        self.geometry("500x300")
        self.resizable(False, False)

        # Zentrieren auf Bildschirm
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 300) // 2
        self.geometry(f"500x300+{x}+{y}")

        # Kein Fensterrahmen (borderless)
        self.overrideredirect(True)

        # Hintergrund
        self.configure(fg_color=("#f0f0f0", "#1a1a1a"))

        # Hauptcontainer
        main_frame = ctk.CTkFrame(
            self,
            fg_color=("#ffffff", "#2b2b2b"),
            corner_radius=15,
            border_width=2,
            border_color=("#0078d4", "#0078d4")
        )
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # App-Name
        app_name = ctk.CTkLabel(
            main_frame,
            text="CO₂-Bilanzierer",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=("#0078d4", "#4da6ff")
        )
        app_name.pack(pady=(40, 10))

        # Untertitel
        subtitle = ctk.CTkLabel(
            main_frame,
            text="Ökobilanzierung nach ABC-Entwurfstafeln",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray70")
        )
        subtitle.pack(pady=(0, 30))

        # Lade-Animation (Progressbar)
        self.progress = ctk.CTkProgressBar(
            main_frame,
            width=350,
            height=6,
            mode="indeterminate"
        )
        self.progress.pack(pady=20)
        self.progress.start()

        # Status-Text
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="Initialisiere...",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray60")
        )
        self.status_label.pack(pady=10)

        # Version
        version_label = ctk.CTkLabel(
            main_frame,
            text=f"Version {self.version}",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray70")
        )
        version_label.pack(side="bottom", pady=20)

        # Immer im Vordergrund
        self.attributes("-topmost", True)

        # Update GUI
        self.update()

    def update_status(self, status_text: str):
        """
        Aktualisiert den Status-Text

        Args:
            status_text: Neuer Status-Text (z.B. "Lade CSV-Datenbank...")
        """
        self.status_label.configure(text=status_text)
        self.update()

    def close(self):
        """Schließt das Splash-Screen"""
        self.progress.stop()
        self.destroy()

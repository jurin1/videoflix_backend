#!/usr/bin/env python
import subprocess
import sys

def run_git_command(command):
    """Führt einen Git-Befehl aus und gibt die Ausgabe zurück"""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Ausführen von {' '.join(command)}: {e}")
        print(f"❌ Error-Ausgabe: {e.stderr}")
        sys.exit(1)

def main():
    # Standard-Commit-Nachricht setzen
    commit_message = "Update"
    
    # Wenn ein Argument übergeben wurde, verwende es als Commit-Nachricht
    if len(sys.argv) > 1:
        commit_message = sys.argv[1]
    
    # Änderungen hinzufügen
    print("📦 Füge alle Änderungen hinzu...")
    run_git_command(["git", "add", "."])
    
    # Commit erstellen
    print(f'💾 Erstelle Commit mit Nachricht: "{commit_message}"...')
    run_git_command(["git", "commit", "-m", commit_message])
    
    # Änderungen pushen
    print("🚀 Pushe Änderungen zum Remote-Repository...")
    run_git_command(["git", "push"])
    
    print("✅ Fertig! Alle Änderungen wurden aktualisiert, committed und gepusht.")

if __name__ == "__main__":
    main()
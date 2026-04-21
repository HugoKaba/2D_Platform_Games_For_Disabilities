# Rendre le jeu téléchargeable par tous

## 1) Construire l'app macOS (.app)

```bash
source .venv/bin/activate
./build_macos.sh
```

Sortie:
- `dist/MiniMarioAR.app`

## 2) Faire une archive à partager

```bash
zip -r MiniMarioAR-mac.zip MiniMarioAR.app
```

Partage le fichier:
- `MiniMarioAR-mac.zip`

## 3) Publier (simple)

Option A (recommandé pour la classe):
- Uploader le zip sur Google Drive / Dropbox / WeTransfer
- Donner le lien

Option B (plus propre):
- Créer un repo GitHub
- Aller dans "Releases"
- Uploader `MiniMarioAR-mac.zip`

## 4) Windows (si besoin)

Le build Windows doit être généré depuis un PC Windows avec les mêmes commandes PyInstaller.

Commande Windows (PowerShell):

```powershell
py -m pip install pyinstaller
py -m PyInstaller --noconfirm --clean --windowed --name MiniMarioAR main.py
```

Sortie:
- `dist\\MiniMarioAR\\MiniMarioAR.exe`

## 5) Note importante pour vos testeurs

Au premier lancement macOS, si message de sécurité:
- Réglages Système > Confidentialité et sécurité > "Ouvrir quand même"

Puis autoriser:
- Caméra
- Microphone

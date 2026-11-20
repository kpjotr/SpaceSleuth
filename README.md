# SpaceSleuth / TárhelyNyomozó

**SpaceSleuth** is a small, Windows-friendly Python tool for finding what uses the most disk space. It scans a selected drive or folder recursively and lists the 30 largest files and folders.

**A SpaceSleuth egy egyszerű, Windows-kompatibilis Python eszköz**, amely rekurzívan átvizsgál egy kiválasztott meghajtót vagy mappát, és megmutatja a 30 legnagyobb fájlt és mappát.

## Features / Funkciók

- Terminal and graphical (Tkinter) interface / Terminálos és grafikus (Tkinter) felület
- Top 30 largest files and folders / TOP 30 legnagyobb fájl és mappa
- Live scan status / Futás közben frissülő állapotjelzés
- Skips unreadable items and reports their count / Kihagyja a nem olvasható elemeket, és jelzi a számukat
- Does not follow symbolic links during scanning / A vizsgálatkor nem követ szimbolikus hivatkozásokat
- Optional UTF-8 CSV export / Opcionális UTF-8 CSV-export
- Multi-select and deletion from the GUI / Több elem kijelölése és törlése a GUI-ból

## Requirements / Követelmények

- Windows
- Python 3.8 or newer / Python 3.8 vagy újabb
- No third-party packages are required. / Nincs szükség külső csomagokra.

Check Python from PowerShell or Command Prompt / Python ellenőrzése PowerShellben vagy Parancssorban:

```powershell
python --version
```

## Files / Fájlok

```text
outputs/
├── lemezterulet_elemzo.py       # terminal scanner / terminálos elemző
└── lemezterulet_elemzo_gui.py   # graphical application / grafikus alkalmazás
```

## Terminal usage / Terminálos használat

Scan drive `C:` / A `C:` meghajtó vizsgálata:

```powershell
python outputs\lemezterulet_elemzo.py C:\
```

Scan a folder / Egy mappa vizsgálata:

```powershell
python outputs\lemezterulet_elemzo.py "C:\Users\YourName\Downloads"
```

Start without a path to be prompted for one / Útvonal nélkül indítva a program rákérdez a vizsgálandó helyre:

```powershell
python outputs\lemezterulet_elemzo.py
```

Export the results to CSV / Eredmények exportálása CSV-be:

```powershell
python outputs\lemezterulet_elemzo.py C:\ --csv space-report.csv
```

## Graphical application / Grafikus alkalmazás

Launch the GUI / GUI indítása:

```powershell
python outputs\lemezterulet_elemzo_gui.py
```

1. Select a drive or folder with **Browse / Tallózás**.
2. Click **Start scan / Vizsgálat indítása**.
3. Select one or more results with Ctrl or Shift.
4. Use **Export CSV / CSV exportálása** to save the displayed top lists, if needed.

1. Válassz ki egy meghajtót vagy mappát a **Tallózás** gombbal.
2. Kattints a **Vizsgálat indítása** gombra.
3. Ctrl vagy Shift segítségével jelölj ki egy vagy több eredményt.
4. Szükség esetén a **CSV exportálása** gombbal mentsd ki a TOP-listákat.

## Important: deletion / Fontos: törlés

The scanner itself performs **read-only** operations. The GUI additionally provides **permanent deletion** for selected files and folders after a confirmation dialog.

- Deleted items **do not go to the Recycle Bin**. / A törölt elemek **nem kerülnek a Lomtárba**.
- Deletion cannot be undone from the app. / A törlés az alkalmazásból nem vonható vissza.
- The folder selected as the scan root cannot be deleted from the app. / A vizsgálat kiinduló mappája nem törölhető az alkalmazásból.
- Always check the selected paths in the confirmation dialog. / A jóváhagyás előtt mindig ellenőrizd a kijelölt útvonalakat.

## Notes / Megjegyzések

- A full-drive scan can take some time. / Egy teljes meghajtó vizsgálata eltarthat egy ideig.
- Protected or unavailable items are skipped; the final status shows how many. / A védett vagy nem elérhető elemek kimaradnak; ezek számát a végső állapot jelzi.
- CSV uses UTF-8 with BOM for convenient opening in Microsoft Excel. / A CSV UTF-8 BOM kódolást használ, így Microsoft Excelben is kényelmesen megnyitható.

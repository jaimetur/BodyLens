# Import data

To bring a BodyLens backup into your account: one from the previous version or one you downloaded yourself.

## Where
**Settings → Data and backups → Import a backup…** (it is the only place).

## Which files it accepts
- **Full backup (JSON)**: the one you download in that same section with **Download full copy**.
- **`snap.json`**: the copy of all the data kept by the previous page. If it contains several profiles, you are first asked **whose data** you are importing: each person imports their own from their own account using the same file.

## How it is imported
- Before importing you see a summary of what the backup contains (weigh-ins, activity, sleep, meals, measurements…).
- **Merge with the current data**: adds what is missing; if a day is in both places, the backup's version is kept.
- **Replace all**: leaves your data exactly as in the backup (asks for confirmation).
- What you import is saved to your account on the server immediately.

## From the console (administration)
```
docker exec bodylens python -m app.data.importer /data/import/snap.json --usuario <usuario> [--perfil <id>] [--con-perfiles]
```

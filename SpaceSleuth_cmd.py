#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Csak olvasási műveleteket végző, Windows-kompatibilis lemezterület-elemző."""

import argparse
import csv
import heapq
import os
import sys
import time
from pathlib import Path


TOP_COUNT = 30


def human_size(size: int) -> str:
    """Bájtokból könnyen olvasható méretet készít."""
    units = ("B", "KB", "MB", "GB", "TB", "PB")
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def keep_largest(heap, size: int, path: str) -> None:
    """Legfeljebb TOP_COUNT rekordot tart meg egy min-kupacban."""
    record = (size, path)
    if len(heap) < TOP_COUNT:
        heapq.heappush(heap, record)
    elif record > heap[0]:
        heapq.heapreplace(heap, record)


def scan(root: Path, progress=None):
    """Bejárja a gyökérmappát; (fájlok, mappák, statisztika) eredményt ad."""
    file_heap, dir_heap = [], []
    stats = {"files": 0, "dirs": 0, "errors": 0}
    last_progress = 0.0

    # A második (False) állapot a mappa bejárása után számolja ki annak méretét.
    stack = [(root, None, True)]
    sizes = {}

    while stack:
        path, parent, entering = stack.pop()
        now = time.monotonic()
        if now - last_progress >= 0.35:
            if progress:
                progress(stats.copy())
            else:
                print(
                    f"\rVizsgálat: {stats['files']:,} fájl, {stats['dirs']:,} mappa, "
                    f"{stats['errors']:,} kihagyott elem...",
                    end="",
                    flush=True,
                )
            last_progress = now

        if not entering:
            size = sizes.get(path, 0)
            if parent is not None:
                sizes[parent] = sizes.get(parent, 0) + size
            keep_largest(dir_heap, size, str(path))
            continue

        sizes[path] = 0
        stats["dirs"] += 1
        stack.append((path, parent, False))
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        # Linkeket nem követünk, így nem lesz végtelen ciklus vagy külső bejárás.
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append((Path(entry.path), path, True))
                        else:
                            size = entry.stat(follow_symlinks=False).st_size
                            stats["files"] += 1
                            sizes[path] += size
                            keep_largest(file_heap, size, entry.path)
                    except (OSError, PermissionError):
                        stats["errors"] += 1
        except (OSError, PermissionError):
            stats["errors"] += 1

    if not progress:
        print("\r" + " " * 100 + "\r", end="")
    files = sorted(file_heap, reverse=True)
    directories = sorted(dir_heap, reverse=True)
    return files, directories, stats


def print_section(title: str, records) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    if not records:
        print("Nincs megjeleníthető elem.")
        return
    for index, (size, path) in enumerate(records, 1):
        print(f"{index:>2}. {human_size(size):>10}  {path}")


def write_csv(filename: Path, files, directories) -> None:
    with filename.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(("Típus", "Helyezés", "Méret (bájt)", "Méret", "Elérési út"))
        for kind, rows in (("Fájl", files), ("Mappa", directories)):
            for rank, (size, path) in enumerate(rows, 1):
                writer.writerow((kind, rank, size, human_size(size), path))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Megkeresi a 30 legnagyobb fájlt és mappát. Nem módosít fájlokat."
    )
    parser.add_argument(
        "path", nargs="?", help="Vizsgálandó meghajtó vagy mappa, például C:\\ vagy C:\\Felhasznalok"
    )
    parser.add_argument("--csv", metavar="FAJL", help="Opcionális CSV-export fájlneve vagy útvonala")
    args = parser.parse_args()

    raw_path = args.path or input("Vizsgálandó meghajtó vagy mappa: ").strip().strip('"')
    root = Path(raw_path).expanduser()
    if not root.is_dir():
        print(f"Hiba: nem létező vagy nem elérhető mappa: {root}", file=sys.stderr)
        return 2

    print(f"Csak olvasási bejárás indul: {root}")
    started = time.monotonic()
    files, directories, stats = scan(root)
    elapsed = time.monotonic() - started

    print_section("TOP 30 legnagyobb fájl", files)
    print_section("TOP 30 legnagyobb mappa", directories)
    print(
        f"\nKész: {stats['files']:,} fájl, {stats['dirs']:,} mappa, "
        f"{stats['errors']:,} jogosultsági/olvasási hiba kihagyva. ({elapsed:.1f} mp)"
    )
    if args.csv:
        target = Path(args.csv).expanduser()
        try:
            write_csv(target, files, directories)
            print(f"CSV elkészült: {target}")
        except OSError as error:
            print(f"A CSV nem írható: {error}", file=sys.stderr)
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

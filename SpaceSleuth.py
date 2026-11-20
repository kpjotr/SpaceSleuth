#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windowsos Tkinter felület a lemezterulet_elemzo.py számára.

A kiválasztott elemek törlése végleges. A program a törléshez nem használ
külső parancsot és nem követ szimbolikus hivatkozásokat a vizsgálatkor.
"""

import os
import queue
import shutil
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from lemezterulet_elemzo import TOP_COUNT, human_size, scan, write_csv


class DiskAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lemezterület-elemző")
        self.minsize(900, 580)
        self.path = tk.StringVar(value=str(Path.home()))
        self.status = tk.StringVar(value="Válassz egy mappát, majd indítsd a vizsgálatot.")
        self.root_path = None
        self.files, self.directories = [], []
        self.events = queue.Queue()
        self._build()
        self.after(150, self._drain_events)

    def _build(self):
        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")
        ttk.Label(top, text="Vizsgálandó mappa vagy meghajtó:").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.path).grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(3, 0))
        ttk.Button(top, text="Tallózás…", command=self.choose_folder).grid(row=1, column=1, pady=(3, 0))
        self.scan_button = ttk.Button(top, text="Vizsgálat indítása", command=self.start_scan)
        self.scan_button.grid(row=1, column=2, padx=(8, 0), pady=(3, 0))
        top.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.pack(fill="x", padx=12)
        ttk.Label(self, textvariable=self.status, padding=(12, 5)).pack(fill="x")

        content = ttk.Panedwindow(self, orient="horizontal")
        content.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.file_tree = self._make_tree(content, "TOP 30 legnagyobb fájl")
        self.dir_tree = self._make_tree(content, "TOP 30 legnagyobb mappa")

        bottom = ttk.Frame(self, padding=(12, 0, 12, 12))
        bottom.pack(fill="x")
        ttk.Label(bottom, text="Több sort is kijelölhetsz Ctrl vagy Shift használatával.").pack(side="left")
        ttk.Button(bottom, text="CSV exportálása…", command=self.export_csv).pack(side="right")
        self.delete_button = ttk.Button(bottom, text="Kijelöltek végleges törlése…", command=self.delete_selected)
        self.delete_button.pack(side="right", padx=(0, 8))

    def _make_tree(self, parent, title):
        frame = ttk.Labelframe(parent, text=title, padding=6)
        tree = ttk.Treeview(frame, columns=("size", "path"), show="headings", selectmode="extended")
        tree.heading("size", text="Méret")
        tree.heading("path", text="Elérési út")
        tree.column("size", width=105, stretch=False, anchor="e")
        tree.column("path", width=370, stretch=True)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        parent.add(frame, weight=1)
        return tree

    def choose_folder(self):
        selected = filedialog.askdirectory(initialdir=self.path.get() or str(Path.home()))
        if selected:
            self.path.set(selected)

    def start_scan(self):
        root = Path(self.path.get().strip().strip('"')).expanduser()
        if not root.is_dir():
            messagebox.showerror("Nem található mappa", f"Ez a mappa vagy meghajtó nem érhető el:\n{root}")
            return
        self.root_path = root.resolve()
        self._clear_trees()
        self.scan_button.configure(state="disabled")
        self.progress.start(12)
        self.status.set("Vizsgálat folyamatban…")
        threading.Thread(target=self._scan_worker, args=(root,), daemon=True).start()

    def _scan_worker(self, root):
        try:
            files, directories, stats = scan(root, progress=lambda s: self.events.put(("progress", s)))
            self.events.put(("complete", files, directories, stats))
        except Exception as error:  # Váratlan, például meghajtó leválasztása.
            self.events.put(("error", str(error)))

    def _drain_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "progress":
                    stats = event[1]
                    self.status.set(f"Vizsgálat: {stats['files']:,} fájl, {stats['dirs']:,} mappa, {stats['errors']:,} kihagyva…")
                elif event[0] == "complete":
                    self.files, self.directories, stats = event[1:]
                    self._show_results()
                    self.progress.stop()
                    self.scan_button.configure(state="normal")
                    self.status.set(f"Kész: {stats['files']:,} fájl, {stats['dirs']:,} mappa, {stats['errors']:,} kihagyva.")
                else:
                    self.progress.stop()
                    self.scan_button.configure(state="normal")
                    self.status.set("A vizsgálat nem fejeződött be.")
                    messagebox.showerror("Vizsgálati hiba", event[1])
        except queue.Empty:
            pass
        self.after(150, self._drain_events)

    def _clear_trees(self):
        for tree in (self.file_tree, self.dir_tree):
            tree.delete(*tree.get_children())

    def _show_results(self):
        self._clear_trees()
        for tree, records in ((self.file_tree, self.files), (self.dir_tree, self.directories)):
            for number, (size, path) in enumerate(records, 1):
                # A mappát, amelyet épp átvizsgáltunk, nem ajánljuk törlésre.
                if tree is self.dir_tree and Path(path).resolve() == self.root_path:
                    continue
                tree.insert("", "end", iid=f"{id(tree)}-{number}", values=(human_size(size), path))

    def _selected_paths(self):
        selected = []
        for tree in (self.file_tree, self.dir_tree):
            for item in tree.selection():
                selected.append(Path(tree.item(item, "values")[1]))
        # Ha egy kijelölt mappa már tartalmaz egy másik kijelölt elemet, csak a mappát töröljük.
        result = []
        for path in selected:
            try:
                contained = any(path != parent and os.path.commonpath((str(path), str(parent))) == str(parent) for parent in selected)
            except ValueError:
                contained = False
            if not contained and path not in result:
                result.append(path)
        return result

    def delete_selected(self):
        paths = self._selected_paths()
        if not paths:
            messagebox.showinfo("Nincs kijelölés", "Jelölj ki legalább egy fájlt vagy mappát.")
            return
        preview = "\n".join(str(path) for path in paths[:5])
        more = "\n…" if len(paths) > 5 else ""
        if not messagebox.askyesno(
            "Végleges törlés megerősítése",
            f"{len(paths)} kijelölt elem végleg törlődik. Ez nem kerül a Lomtárba.\n\n{preview}{more}\n\nFolytatod?",
            icon="warning",
        ):
            return
        failed = []
        for path in paths:
            try:
                if self.root_path and path.resolve() == self.root_path:
                    raise ValueError("A vizsgálat gyökérmappája nem törölhető ebből az alkalmazásból.")
                if path.is_dir() and not path.is_symlink():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            except (OSError, ValueError) as error:
                failed.append(f"{path}: {error}")
        self._remove_missing_rows()
        if failed:
            messagebox.showwarning("Néhány elem nem törölhető", "\n".join(failed[:10]))
        else:
            self.status.set(f"{len(paths)} elem végleg törölve.")

    def _remove_missing_rows(self):
        for tree in (self.file_tree, self.dir_tree):
            for item in tree.get_children():
                if not Path(tree.item(item, "values")[1]).exists():
                    tree.delete(item)

    def export_csv(self):
        if not (self.files or self.directories):
            messagebox.showinfo("Nincs eredmény", "Előbb indíts vizsgálatot.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=(("CSV-fájl", "*.csv"),))
        if filename:
            try:
                write_csv(Path(filename), self.files, self.directories)
                self.status.set(f"CSV elkészült: {filename}")
            except OSError as error:
                messagebox.showerror("Exportálási hiba", str(error))


if __name__ == "__main__":
    DiskAnalyzerApp().mainloop()

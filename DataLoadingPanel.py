import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import matplotlib.pyplot as plt
import traceback
from Tooltip import Tooltip
from PreprocessingPanel import PreprocessingPanel

try:
    from HspyPrep import HspyPrep, PLData, SingleSpectrumData
    from SpecVision import CondAns
except ImportError:
    try:
        messagebox.showerror(
            "Import Error",
            "Could not import HspyPrep or SpecVision.\n"
            "Make sure HspyPrep.py and SpecVision.py are in the same directory."
        )
    except Exception:
        print("ImportError: Could not import HspyPrep/CondAns")
    raise


_MODES = [
    ("series",     "CL Comparative Series",
     "Load multiple CL experiments from a root folder.\n"
     "Each sub-folder whose name contains 'HYP' is treated as one experiment."),
    ("single",     "Single CL Experiment",
     "Load one CL measurement folder (must contain HYPCard.sur)."),
    ("pl_map",     "Single PL Map  (.hspy)",
     "Load a HyperSpy PL hyperspectral map file (.hspy).\n"
     "Axes are auto-detected; data is reshaped to (rows × cols × λ)."),
    ("csv_single", "Single Spectrum  (CSV)",
     "Load a two-column CSV file (wavelength | intensity).\n"
     "An optional header row is detected automatically."),
]


class DataLoadingPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("SpecVision — Step 1: Load Data")
        self.root.geometry("880x800")

        # ── state ─────────────────────────────────────────────────────────
        self.data_path = tk.StringVar()
        self.bg_file   = tk.StringVar()
        self.dict_of_files = {}
        self.load_mode = tk.StringVar(value="series")

        # ── main container ────────────────────────────────────────────────
        outer = ttk.Frame(self.root, padding="14 12 14 10")
        outer.pack(fill=tk.BOTH, expand=True)

        # ── header ────────────────────────────────────────────────────────
        hdr = ttk.Frame(outer)
        hdr.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(hdr, text="SpecVision", style="AppTitle.TLabel").pack(side=tk.LEFT)
        ttk.Label(hdr, text="  /  Data Loader", style="AppSub.TLabel").pack(
            side=tk.LEFT, pady=(6, 0))
        ttk.Separator(outer, orient="horizontal").pack(fill=tk.X, pady=(2, 10))

        # ── Step 1 — mode selection ───────────────────────────────────────
        mode_frame = ttk.LabelFrame(outer, text=" Step 1 — Select Data Type ", padding="10 8")
        mode_frame.pack(fill=tk.X, pady=(0, 8))

        for value, label, tip in _MODES:
            row = ttk.Frame(mode_frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Radiobutton(
                row, text=label,
                variable=self.load_mode, value=value,
                command=self.on_mode_change
            ).pack(side=tk.LEFT, padx=(4, 0))
            info = ttk.Label(row, text=" ⓘ", foreground="#718096", cursor="question_arrow")
            info.pack(side=tk.LEFT)
            Tooltip(info, text=tip, wraplength=360)

        # ── Step 2 — data selection ───────────────────────────────────────
        self.ctrl_frame = ttk.LabelFrame(outer, text=" Step 2 — Select Data ", padding="10 8")
        self.ctrl_frame.pack(fill=tk.X, pady=(0, 8))

        # data path row
        path_row = ttk.Frame(self.ctrl_frame)
        path_row.pack(fill=tk.X, pady=(2, 4))
        self.btn_path = ttk.Button(path_row, text="Browse…", command=self.select_data_path, width=18)
        self.btn_path.pack(side=tk.LEFT, padx=(0, 8))
        self.lbl_path = ttk.Label(
            path_row, textvariable=self.data_path,
            relief="groove", anchor="w", padding="4 3",
            width=58, foreground="#4A5568"
        )
        self.lbl_path.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # background file row (CL modes only)
        self.bg_row = ttk.Frame(self.ctrl_frame)
        self.bg_row.pack(fill=tk.X, pady=(0, 4))
        self.btn_bg = ttk.Button(
            self.bg_row, text="Background File…",
            command=self.select_bg_file, width=18
        )
        self.btn_bg.pack(side=tk.LEFT, padx=(0, 8))
        self.lbl_bg = ttk.Label(
            self.bg_row, textvariable=self.bg_file,
            relief="groove", anchor="w", padding="4 3",
            width=58, foreground="#4A5568"
        )
        self.lbl_bg.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # load button row
        load_row = ttk.Frame(self.ctrl_frame)
        load_row.pack(fill=tk.X, pady=(4, 2))
        self.btn_load = ttk.Button(
            load_row, text="  Load Data  ",
            command=self.load_data, style="Accent.TButton"
        )
        self.btn_load.pack(side=tk.RIGHT)

        # ── Step 3 — detected datasets ────────────────────────────────────
        self.list_frame = ttk.LabelFrame(
            outer, text=" Step 3 — Detected Datasets ", padding="6 4"
        )
        self.list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        list_inner = ttk.Frame(self.list_frame)
        list_inner.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            list_inner,
            columns=("type", "status"),
            height=10, selectmode="extended"
        )
        self.tree.heading("#0", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("status", text="Status / Info")
        self.tree.column("#0",      width=240, minwidth=140)
        self.tree.column("type",    width=130, minwidth=80)
        self.tree.column("status",  width=320, minwidth=120)

        vsb = ttk.Scrollbar(list_inner, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        vsb.pack(side=tk.LEFT, fill=tk.Y)

        btn_col = ttk.Frame(list_inner)
        btn_col.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0))
        ttk.Button(btn_col, text="Verify",  command=self.verify_selected,  width=10).pack(pady=(6, 3), fill=tk.X)
        ttk.Button(btn_col, text="Rename",  command=self.rename_selected,  width=10).pack(pady=3,      fill=tk.X)

        info_lbl = ttk.Label(self.list_frame, text="ⓘ", foreground="#718096", cursor="question_arrow")
        info_lbl.place(relx=1.0, x=-24, y=4)
        Tooltip(info_lbl, text="Ctrl/Shift to multi-select.\nDrag rows to reorder (order matters for comparative analysis).")

        # ── drag-and-drop ─────────────────────────────────────────────────
        self._dragging_iid = None
        self._setup_tree_drag_and_drop()

        # ── bottom action bar ─────────────────────────────────────────────
        action_bar = ttk.Frame(outer)
        action_bar.pack(fill=tk.X)
        self.lbl_status = ttk.Label(
            action_bar, text="Status: waiting for data…",
            foreground="#718096"
        )
        self.lbl_status.pack(side=tk.LEFT, padx=4)
        self.btn_preprocess = ttk.Button(
            action_bar, text="Proceed to Preprocessing  →",
            command=self.open_preprocessing_panel,
            style="Accent.TButton", state="disabled"
        )
        self.btn_preprocess.pack(side=tk.RIGHT)

        self.on_mode_change()

    # ── drag-and-drop helpers ─────────────────────────────────────────────

    def _setup_tree_drag_and_drop(self):
        self.tree.bind('<ButtonPress-1>',   self._on_tree_button_press)
        self.tree.bind('<B1-Motion>',        self._on_tree_mouse_drag)
        self.tree.bind('<ButtonRelease-1>', self._on_tree_button_release)

    def _on_tree_button_press(self, event):
        rowid = self.tree.identify_row(event.y)
        self._dragging_iid = rowid if rowid else None

    def _on_tree_mouse_drag(self, event):
        if self._dragging_iid:
            self.tree.after(1, self._drag_feedback, event)

    def _drag_feedback(self, event):
        target = self.tree.identify_row(event.y)
        if not target or target == self._dragging_iid:
            return
        bbox = self.tree.bbox(target)
        where = 'above' if (not bbox or event.y < bbox[1] + bbox[3] // 2) else 'below'
        try:
            self.tree.move(self._dragging_iid, '', self._index_for_move(target, where))
        except tk.TclError:
            pass

    def _index_for_move(self, target, where):
        children = list(self.tree.get_children(''))
        idx = children.index(target)
        return idx if where == 'above' else idx + 1

    def _on_tree_button_release(self, _):
        self._dragging_iid = None

    # ── mode change ───────────────────────────────────────────────────────

    def on_mode_change(self):
        mode = self.load_mode.get()
        is_cl = mode in ("series", "single")

        labels = {
            "series":     ("Select Root Folder",    " Step 3 — Detected CL Experiments "),
            "single":     ("Select Experiment Folder", " Step 3 — Detected CL Experiment "),
            "pl_map":     ("Select .hspy File",     " Step 3 — Loaded PL Map "),
            "csv_single": ("Select CSV File",        " Step 3 — Loaded Spectrum "),
        }
        btn_text, lf_text = labels.get(mode, ("Browse…", " Step 3 — Detected Datasets "))
        self.btn_path.config(text=btn_text)
        self.list_frame.config(text=lf_text)

        if is_cl:
            self.btn_bg.config(state="normal")
            self.lbl_bg.config(relief="groove")
        else:
            self.btn_bg.config(state="disabled")
            self.bg_file.set("")
            self.lbl_bg.config(relief="flat")

    # ── file / folder pickers ─────────────────────────────────────────────

    def select_data_path(self):
        mode = self.load_mode.get()
        if mode == "series":
            path = filedialog.askdirectory(title="Select Root Folder")
        elif mode == "single":
            path = filedialog.askdirectory(title="Select Experiment Folder")
        elif mode == "pl_map":
            path = filedialog.askopenfilename(
                title="Select PL Map File",
                filetypes=[("HyperSpy files", "*.hspy"), ("All files", "*.*")]
            )
        elif mode == "csv_single":
            path = filedialog.askopenfilename(
                title="Select Spectrum CSV",
                filetypes=[("CSV / text files", "*.csv *.txt"), ("All files", "*.*")]
            )
        else:
            path = None
        if path:
            self.data_path.set(path)

    def select_bg_file(self):
        path = filedialog.askopenfilename(
            title="Select Background File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            self.bg_file.set(path)

    # ── loading ───────────────────────────────────────────────────────────

    def load_data(self):
        if not self.data_path.get():
            messagebox.showerror("Error", "Please select a data path first.")
            return
        self.lbl_status.config(text="Loading… please wait.")
        self.btn_load.config(state="disabled")
        self.tree.delete(*self.tree.get_children())
        self.dict_of_files.clear()
        try:
            mode = self.load_mode.get()
            dispatch = {
                "series":     self.load_series_experiment,
                "single":     self.load_single_experiment,
                "pl_map":     self.load_pl_map,
                "csv_single": self.load_csv_spectrum,
            }
            dispatch[mode]()
            if self.dict_of_files:
                self.btn_preprocess.config(state="normal")
        except Exception as e:
            messagebox.showerror("Loading Failed", f"{e}\n\n{traceback.format_exc()}")
            self.lbl_status.config(text="Status: error — see dialog.")
        finally:
            self.btn_load.config(state="normal")

    def load_series_experiment(self):
        root_path = self.data_path.get()
        for name in os.listdir(root_path):
            if 'HYP' in name:
                exp_path = os.path.join(root_path, name, '')
                try:
                    obj = HspyPrep(exp_path, step=1, whole_seconds=64 * 64, contain_bg=True)
                    self.dict_of_files[name] = obj
                    self.tree.insert("", "end", text=name, values=("CL Map", "Loaded"), iid=name)
                except Exception as e:
                    self.tree.insert("", "end", text=name, values=("CL Map", f"Error: {e}"))
        self.lbl_status.config(text=f"Series loaded — {len(self.dict_of_files)} experiment(s).")

    def load_single_experiment(self):
        exp_path = self.data_path.get()
        name = os.path.basename(os.path.normpath(exp_path))
        try:
            obj = HspyPrep(exp_path + '/', step=1, whole_seconds=64 * 64, contain_bg=False)
            self.dict_of_files[name] = obj
            self.tree.insert("", "end", text=name, values=("CL Map", "Loaded"), iid=name)
        except Exception as e:
            self.tree.insert("", "end", text=name, values=("CL Map", f"Error: {e}"))
        self.lbl_status.config(text=f"CL experiment '{name}' loaded.")

    def load_pl_map(self):
        file_path = self.data_path.get()
        name = os.path.splitext(os.path.basename(file_path))[0]
        try:
            obj = PLData(file_path)
            self.dict_of_files[name] = obj
            s = obj.get_numpy_spectra().shape
            wl = obj.get_wavelengths()
            status = f"{s[0]}×{s[1]} px  |  {s[2]} λ pts  |  {wl[0]:.0f}–{wl[-1]:.0f} nm"
            self.tree.insert("", "end", text=name, values=("PL Map", status), iid=name)
        except Exception as e:
            self.tree.insert("", "end", text=name, values=("PL Map", f"Error: {e}"))
        self.lbl_status.config(text=f"PL map '{name}' loaded.")

    def load_csv_spectrum(self):
        file_path = self.data_path.get()
        name = os.path.splitext(os.path.basename(file_path))[0]
        try:
            obj = SingleSpectrumData(file_path)
            self.dict_of_files[name] = obj
            wl = obj.get_wavelengths()
            status = f"{len(wl)} pts  |  {wl[0]:.1f}–{wl[-1]:.1f} nm"
            self.tree.insert("", "end", text=name, values=("Single Spectrum", status), iid=name)
        except Exception as e:
            self.tree.insert("", "end", text=name, values=("Single Spectrum", f"Error: {e}"))
        self.lbl_status.config(text=f"Single spectrum '{name}' loaded.")

    # ── tree helpers ──────────────────────────────────────────────────────

    def _ordered_selection(self):
        selected = set(self.tree.selection())
        return [iid for iid in self.tree.get_children("") if iid in selected]

    def verify_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select an experiment to verify.")
            return
        iid = self._ordered_selection()[0]
        name = self.tree.item(iid, "text")
        obj = self.dict_of_files.get(name)
        if obj is None:
            messagebox.showerror("Error", f"No loaded data for '{name}'.")
            return
        try:
            data = obj.get_numpy_spectra()
            wl   = obj.get_wavelengths()
            live = obj.get_live_scan()
            n_plots = 2 if live is not None else 1
            fig, axes = plt.subplots(1, n_plots, figsize=(5 * n_plots + 1, 4))
            if n_plots == 1:
                axes = [axes]
            if live is not None:
                axes[0].imshow(live, cmap='viridis', aspect='auto')
                axes[0].set_title("Integrated Intensity Map")
                axes[0].set_xlabel("X (px)")
                axes[0].set_ylabel("Y (px)")
                axes[0].grid(False)
            cy, cx = data.shape[0] // 2, data.shape[1] // 2
            axes[-1].plot(wl, data[cy, cx, :], linewidth=1.4)
            axes[-1].set_title(f"Sample spectrum @ ({cy}, {cx})")
            axes[-1].set_xlabel("Wavelength (nm)")
            axes[-1].set_ylabel("Intensity (a.u.)")
            axes[-1].grid(True, linestyle="--", alpha=0.5)
            fig.suptitle(name, fontsize=12, fontweight="bold")
            fig.tight_layout()
            plt.show()
        except Exception as e:
            messagebox.showerror("Plot Error", f"{e}\n\n{traceback.format_exc()}")

    def rename_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Select an experiment to rename.")
            return
        if len(selected) > 1:
            messagebox.showinfo("Info", "Select only one experiment to rename.")
            return
        iid = selected[0]
        old_name = self.tree.item(iid, "text")
        new_name = simpledialog.askstring(
            "Rename", f"New name for '{old_name}':", parent=self.root
        )
        if new_name and new_name != old_name:
            if new_name in self.dict_of_files:
                messagebox.showerror("Error", f"'{new_name}' already exists.")
                return
            values = self.tree.item(iid, 'values')
            index  = list(self.tree.get_children('')).index(iid)
            self.tree.delete(iid)
            self.tree.insert('', index, text=new_name, values=values, iid=new_name)
            self.dict_of_files[new_name] = self.dict_of_files.pop(old_name)

    # ── proceed ───────────────────────────────────────────────────────────

    def open_preprocessing_panel(self):
        selected_ids = self.tree.selection()
        if not selected_ids:
            messagebox.showerror("Error", "Select one or more datasets to process.")
            return
        ordered = self._ordered_selection()
        analysis_dict = {
            self.tree.item(iid, "text"): self.dict_of_files[self.tree.item(iid, "text")]
            for iid in ordered
            if self.tree.item(iid, "text") in self.dict_of_files
        }
        if not analysis_dict:
            messagebox.showerror("Error", "Could not find data for selected items.")
            return
        try:
            ref_key = next(iter(analysis_dict))
            self.root.withdraw()
            PreprocessingPanel(
                self.root, analysis_dict, ref_key,
                self.bg_file.get(), self.load_mode.get()
            )
        except Exception as e:
            messagebox.showerror(
                "Initialization Error",
                f"Failed to open preprocessing panel:\n{e}\n\n{traceback.format_exc()}"
            )
            self.root.deiconify()

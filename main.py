# main.py  –  Simplic Editor
import os
import sys
import shutil
import subprocess

from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, QPushButton,
    QLineEdit, QFileSystemModel, QTreeView, QFileDialog, QDialog, QComboBox, QCheckBox,
    QDialogButtonBox, QMenu, QAction, QInputDialog, QStackedLayout, QMessageBox, QTextEdit,
    QTabWidget, QSplitter, QTextBrowser, QSizePolicy, QRadioButton
)
from PyQt5.QtCore import Qt, QProcess
from PyQt5.QtGui import QFont


# ──────────────────────────────────────────────────────────────
#  PROJECT EDITOR
# ──────────────────────────────────────────────────────────────
class ProjectEditor(QWidget):
    def __init__(self, path: str, theme: str = "dark"):
        super().__init__()
        self.project_path = path
        self.theme = theme
        self.open_tabs = {}
        self.init_ui()

    # ------------  UI  ------------
    def init_ui(self):
        layout = QVBoxLayout(self)

        # ── Toolbar ──
        toolbar = QHBoxLayout()
        for icon, label in [("▶️", "Run"), ("🔧", "Build"), ("💾", "Save"), ("🐞", "Debug")]:
            btn = QPushButton(f"{icon} {label}")
            btn.setFixedHeight(30)
            toolbar.addWidget(btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Split vertically: [tree + tabs]  /  [preview]
        splitter = QSplitter(Qt.Vertical)
        top_split = QSplitter(Qt.Horizontal)

        # ── File tree ──
        self.model = QFileSystemModel()
        self.model.setRootPath(self.project_path)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.project_path))
        self.tree.doubleClicked.connect(self.open_file_from_tree)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        # ── Styling based on theme ──
        if self.theme == "dark":
            tree_style = "background-color:#2b2b2b;color:white;"
            tab_style = """
                QTabBar::tab{height:24px;padding:6px;font-weight:bold;font-family:Consolas;
                              background:#3c3f41;color:white;}
                QTabBar::tab:selected{background:#555;color:#fff;border-bottom:2px solid #ffaa00;}
            """
            self.editor_style = "background-color:#1e1e1e;color:#fff;padding:10px;"
            self.preview_style = "background-color:#111;color:#0f0;font-family:Consolas;padding:6px;"
        else:
            tree_style = "background-color:#f0f0f0;color:black;"
            tab_style = """
                QTabBar::tab{height:24px;padding:6px;font-weight:bold;font-family:Consolas;
                              background:#e0e0e0;color:black;}
                QTabBar::tab:selected{background:#ccc;color:#000;border-bottom:2px solid #007acc;}
            """
            self.editor_style = "background-color:#fff;color:#000;padding:10px;"
            self.preview_style = "background-color:#eee;color:#060;font-family:Consolas;padding:6px;"

        self.tree.setStyleSheet(tree_style)
        top_split.addWidget(self.tree)

        # ── Tabs (code editors) ──
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(tab_style)
        top_split.addWidget(self.tabs)
        top_split.setSizes([250, 800])          # initial splitter sizes
        splitter.addWidget(top_split)

        # ── Preview / output pane ──
        self.preview_output = QTextBrowser()
        self.preview_output.setStyleSheet(self.preview_style)
        self.preview_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.preview_output.setMinimumHeight(150)
        splitter.addWidget(self.preview_output)

        layout.addWidget(splitter)

        # ── Toolbar button actions ──
        toolbar.itemAt(0).widget().clicked.connect(self.run_project)
        toolbar.itemAt(1).widget().clicked.connect(self.build_project)
        toolbar.itemAt(2).widget().clicked.connect(self.save_current_file)
        toolbar.itemAt(3).widget().clicked.connect(self.debug_project)

    # ------------  File handling ------------
    def open_file_from_tree(self, index):
        if self.model.isDir(index):
            return
        filepath = self.model.filePath(index)
        filename = os.path.basename(filepath)
        if filename in self.open_tabs:
            self.tabs.setCurrentWidget(self.open_tabs[filename])
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            content = f"Error opening file: {e}"
        editor = QTextEdit()
        editor.setText(content)
        editor.setFontFamily("Consolas")
        editor.setStyleSheet(self.editor_style)
        self.tabs.addTab(editor, filename)
        self.tabs.setCurrentWidget(editor)
        self.open_tabs[filename] = editor

    def save_current_file(self):
        index = self.tabs.currentIndex()
        if index == -1:
            return
        editor = self.tabs.currentWidget()
        filename = self.tabs.tabText(index)
        filepath = os.path.join(self.project_path, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())
        except Exception:
            QMessageBox.critical(self, "Error", "Could not save file.")

    # ------------  Run / Build / Debug ------------
    def run_project(self):
        self.preview_output.clear()
        main_file = os.path.join(self.project_path, "main.py")
        if not os.path.exists(main_file):
            self.preview_output.setText("⚠️ main.py not found.")
            return

        process = QProcess(self)
        process.setProgram("python")
        process.setArguments([main_file])
        process.setWorkingDirectory(self.project_path)
        process.readyReadStandardOutput.connect(
            lambda: self.preview_output.append(process.readAllStandardOutput().data().decode()))
        process.readyReadStandardError.connect(
            lambda: self.preview_output.append(process.readAllStandardError().data().decode()))
        process.start()

    def debug_project(self):
        main_file = os.path.join(self.project_path, "main.py")
        if os.path.exists(main_file):
            subprocess.Popen(["python", "-m", "pdb", main_file], cwd=self.project_path)
        else:
            QMessageBox.warning(self, "Debug", "main.py not found.")

    # ------------  BUILD (PyToExe now functional) ------------
    def get_project_type(self) -> str:
        type_path = os.path.join(self.project_path, ".project_type")
        if os.path.exists(type_path):
            with open(type_path, "r") as f:
                return f.read().strip()
        return "PyToExe"

    def build_project(self):
        proj_type = self.get_project_type()

        if proj_type != "PyToExe":
            QMessageBox.information(self, "Coming Soon", f"{proj_type} support is coming soon.")
            return

        # --- PyToExe build logic ---
        exe_path = r"C:\Users\Guddu\AppData\Local\Programs\Python\Python311\Scripts\pyinstaller.exe"
        if not os.path.exists(exe_path):
            QMessageBox.critical(self, "PyInstaller not found",
                                 f"Could not locate PyInstaller at:\n{exe_path}")
            return

        main_file = os.path.join(self.project_path, "main.py")
        if not os.path.isfile(main_file):
            QMessageBox.critical(self, "Build", "main.py not found in project.")
            return

        output_dir = os.path.join(self.project_path, "outputs")
        build_dir = os.path.join(self.project_path, "build")
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(build_dir, exist_ok=True)

        cmd = [
            exe_path, main_file,
            "--distpath", output_dir,
            "--workpath", build_dir,
            "--specpath", build_dir,
            "--noconfirm"
        ]

        try:
            subprocess.run(cmd, cwd=self.project_path, check=True)
            QMessageBox.information(self, "Build", f"Build complete.\n.exe saved in {output_dir}")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Build Failed", f"Error during build:\n{e}")

    # ------------  Tree context-menu helpers ------------
    def show_context_menu(self, position):
        index = self.tree.indexAt(position)
        if not index.isValid():
            return
        menu = QMenu()
        new_action = QAction("New File", self)
        delete_action = QAction("Delete", self)
        rename_action = QAction("Rename", self)
        new_action.triggered.connect(lambda: self.new_file(index))
        delete_action.triggered.connect(lambda: self.delete_item(index))
        rename_action.triggered.connect(lambda: self.rename_item(index))
        menu.addAction(new_action)
        menu.addAction(delete_action)
        menu.addAction(rename_action)
        menu.exec_(self.tree.viewport().mapToGlobal(position))

    def new_file(self, index):
        dir_path = self.model.filePath(index)
        if not os.path.isdir(dir_path):
            dir_path = os.path.dirname(dir_path)
        name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and name:
            open(os.path.join(dir_path, name), "w", encoding="utf-8").close()
            self.tree.setRootIndex(self.model.index(self.project_path))

    def delete_item(self, index):
        path = self.model.filePath(index)
        if QMessageBox.question(self, "Delete", f"Delete {os.path.basename(path)}?") == QMessageBox.Yes:
            shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
            self.tree.setRootIndex(self.model.index(self.project_path))

    def rename_item(self, index):
        path = self.model.filePath(index)
        name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=os.path.basename(path))
        if ok and name:
            os.rename(path, os.path.join(os.path.dirname(path), name))
            self.tree.setRootIndex(self.model.index(self.project_path))


# ──────────────────────────────────────────────────────────────
#  WELCOME / SHELL  (App)
# ──────────────────────────────────────────────────────────────
class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome to Android Studio")
        self.setMinimumSize(1080, 650)
        self.theme = "dark"
        self.ensure_required_folders()

        # One outer stack: welcome screen OR editor
        self.outer_stack = QStackedLayout(self)
        self.init_welcome_screen()
        self.setLayout(self.outer_stack)
        self.apply_dark_theme()

    # ------------  Folders ------------
    def ensure_required_folders(self):
        for folder in ["projects", "utils"]:
            os.makedirs(folder, exist_ok=True)

    # ------------  Welcome screen UI ------------
    def init_welcome_screen(self):
        self.welcome_screen = QWidget()
        layout = QHBoxLayout(self.welcome_screen)

        # Sidebar
        side = QVBoxLayout()
        logo = QLabel("🪶➰"); logo.setFont(QFont("Arial", 28))
        studio = QLabel("Simplic Editor"); studio.setFont(QFont("Arial", 14, QFont.Bold))
        version = QLabel("Unknown Studios SE.A1.2025"); version.setFont(QFont("Arial", 9))
        version.setStyleSheet("color:#aaa;")
        side.addWidget(logo); side.addWidget(studio); side.addWidget(version)
        side.addSpacing(20)

        self.nav_list = QListWidget()
        self.nav_list.addItems(["Projects", "Customize", "Libraries", "Know More"])
        self.nav_list.setFixedWidth(180)
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self.switch_inner_tab)
        side.addWidget(self.nav_list)
        side.addStretch()
        layout.addLayout(side)

        # Inner stack (for Projects / Customize / etc.)
        self.inner_stack = QStackedLayout()
        self.projects_tab = self.make_projects_tab()
        self.inner_stack.addWidget(self.projects_tab)
        self.inner_stack.addWidget(QWidget())  # Customize
        self.inner_stack.addWidget(QWidget())  # Libraries
        self.inner_stack.addWidget(QWidget())  # Know More

        center = QWidget(); center.setLayout(self.inner_stack)
        layout.addWidget(center)

        self.outer_stack.addWidget(self.welcome_screen)

    # --- Projects tab content ---
    def make_projects_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        top = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText("Search projects")
        self.new_btn = QPushButton("New Project"); self.new_btn.clicked.connect(self.create_project)
        self.open_btn = QPushButton("Open"); self.open_btn.clicked.connect(self.open_existing_folder)
        self.clone_btn = QPushButton("Clone Repository")  # placeholder
        top.addWidget(self.search); top.addWidget(self.new_btn)
        top.addWidget(self.open_btn); top.addWidget(self.clone_btn)
        layout.addLayout(top)

        layout.addWidget(QLabel("Projects in /projects:"))

        self.project_view = QTreeView()
        self.project_model = QFileSystemModel()
        self.project_model.setRootPath("projects")
        self.project_view.setModel(self.project_model)
        self.project_view.setRootIndex(self.project_model.index("projects"))
        for col in (1, 2, 3):
            self.project_view.setColumnHidden(col, True)
        layout.addWidget(self.project_view)
        return tab

    # ------------  Navigation & Theme ------------
    def switch_inner_tab(self, index):        # sidebar list → inner stack
        self.inner_stack.setCurrentIndex(index)

    def apply_dark_theme(self):
        self.setStyleSheet("background-color:#2b2b2b;color:white;")
        self.project_view.setStyleSheet("background-color:#3c3f41;color:white;")

    # ------------  Project creation & opening ------------
    def select_project_type(self) -> str | None:
        dlg = QDialog(self); dlg.setWindowTitle("Select Project Type"); dlg.setFixedSize(300, 200)
        vbox = QVBoxLayout(dlg)
        vbox.addWidget(QLabel("Choose a project type:"))

        radio_buttons = {
            "PyToExe": QRadioButton("Python → Executable  (.exe)"),
            "PyToApk": QRadioButton("Python → APK  (Coming Soon)"),
            "KoToApk": QRadioButton("Kotlin → APK  (Coming Soon)")
        }
        radio_buttons["PyToExe"].setChecked(True)
        for rb in radio_buttons.values():
            vbox.addWidget(rb)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        vbox.addWidget(btn_box)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)

        if dlg.exec_() == QDialog.Accepted:
            for key, rb in radio_buttons.items():
                if rb.isChecked():
                    return key
        return None

    def create_project(self):
        proj_type = self.select_project_type()
        if proj_type is None:
            return

        name, ok = QFileDialog.getSaveFileName(self, "New Project Name", "projects/", "")
        if not ok or not name:
            return

        folder_name = os.path.basename(name)
        full_path = os.path.join("projects", folder_name)
        os.makedirs(full_path, exist_ok=True)

        # starter main.py
        with open(os.path.join(full_path, "main.py"), "w", encoding="utf-8") as f:
            f.write("print('Hello from SimplicEditor')\n")

        # record project type
        with open(os.path.join(full_path, ".project_type"), "w") as f:
            f.write(proj_type)

        self.project_view.setRootIndex(self.project_model.index("projects"))

    def open_existing_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder", "projects/")
        if folder:
            self.open_project_editor(folder)

    # ------------  Editor switch-in (replaces welcome) ------------
    def open_project_editor(self, path):
        editor = ProjectEditor(path, self.theme)
        self.outer_stack.addWidget(editor)
        self.outer_stack.setCurrentWidget(editor)
        self.setWindowTitle(f"{os.path.basename(path)} - Android Studio")


# ──────────────────────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = App(); win.show()
    sys.exit(app.exec_())

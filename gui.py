import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLabel, QLineEdit, QPushButton,
    QComboBox, QSpinBox, QFileDialog,
    QTextEdit, QStatusBar,
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QFont

import apitest as bsky


# ── Background worker ──────────────────────────────────────────────────────────

class DownloadWorker(QThread):
    log  = pyqtSignal(str)
    done = pyqtSignal(bool, str)   # (success, message)

    def __init__(self, cfg: dict):
        super().__init__()
        self.cfg    = cfg
        self._stop  = False

    def cancel(self):
        self._stop = True

    def run(self):
        cfg = self.cfg
        try:
            self.log.emit(f"Logging in as {cfg['handle']}…")
            session = bsky.bluesky_login(cfg["handle"], cfg["password"])
            jwt = session["accessJwt"]
            self.log.emit("Login OK.")

            target = cfg["target"] or cfg["handle"]
            self.log.emit(f"Resolving {target}…")
            did = bsky.get_did_for_handle(target, jwt)

            if cfg["mode"] == "Liked Posts":
                items = bsky.fetch_likes_media(
                    jwt, did, max_pages=cfg["pages"], log_fn=self.log.emit
                )
            else:
                items = bsky.fetch_user_gallery(
                    jwt, did, max_pages=cfg["pages"], log_fn=self.log.emit
                )

            media_map = {"Both": "both", "Images Only": "images", "Videos Only": "videos"}
            bsky.download_media(
                items,
                cfg["output"],
                media_type=media_map[cfg["media"]],
                log_fn=self.log.emit,
                cancel_fn=lambda: self._stop,
            )

            if self._stop:
                self.done.emit(False, "Cancelled.")
            else:
                self.done.emit(True, f"Done — {len(items)} posts processed.")

        except Exception as e:
            self.done.emit(False, str(e))


# ── Main window ────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BlueSky Downloader")
        self.setMinimumWidth(580)
        self.worker: DownloadWorker | None = None
        self._build_ui()
        self._load_saved_credentials()

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        layout.addWidget(self._credentials_group())
        layout.addWidget(self._options_group())
        layout.addWidget(self._output_group())
        layout.addLayout(self._buttons_row())
        layout.addWidget(self._log_group())

        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")

    def _credentials_group(self) -> QGroupBox:
        g = QGroupBox("Credentials")
        f = QFormLayout(g)
        self.le_handle = QLineEdit(placeholderText="you.bsky.social")
        self.le_pass   = QLineEdit(placeholderText="App password  (Settings → App Passwords)")
        self.le_pass.setEchoMode(QLineEdit.EchoMode.Password)
        f.addRow("Handle:", self.le_handle)
        f.addRow("App Password:", self.le_pass)
        return g

    def _options_group(self) -> QGroupBox:
        g = QGroupBox("Download Options")
        f = QFormLayout(g)

        self.cb_mode = QComboBox()
        self.cb_mode.addItems(["Liked Posts", "User Gallery"])
        self.cb_mode.currentTextChanged.connect(self._on_mode_changed)

        self.le_target = QLineEdit(placeholderText="Leave blank to use your own account")

        self.cb_media = QComboBox()
        self.cb_media.addItems(["Both", "Images Only", "Videos Only"])

        self.sp_pages = QSpinBox()
        self.sp_pages.setRange(1, 200)
        self.sp_pages.setValue(25)
        self.sp_pages.setSuffix("  pages  (~50 posts each)")

        f.addRow("Mode:", self.cb_mode)
        f.addRow("Target Handle:", self.le_target)
        f.addRow("Media Type:", self.cb_media)
        f.addRow("Max Pages:", self.sp_pages)
        return g

    def _output_group(self) -> QGroupBox:
        g = QGroupBox("Output Folder")
        h = QHBoxLayout(g)
        self.le_output = QLineEdit(bsky.DEFAULT_DOWNLOAD_DIR)
        btn = QPushButton("Browse…")
        btn.setFixedWidth(80)
        btn.clicked.connect(self._browse_output)
        h.addWidget(self.le_output)
        h.addWidget(btn)
        return g

    def _buttons_row(self) -> QHBoxLayout:
        h = QHBoxLayout()
        self.btn_start  = QPushButton("Start Download")
        self.btn_cancel = QPushButton("Cancel")
        for btn in (self.btn_start, self.btn_cancel):
            btn.setFixedHeight(34)
        self.btn_cancel.setEnabled(False)
        self.btn_start.clicked.connect(self._start)
        self.btn_cancel.clicked.connect(self._cancel)
        h.addWidget(self.btn_start)
        h.addWidget(self.btn_cancel)
        return h

    def _log_group(self) -> QGroupBox:
        g = QGroupBox("Log")
        v = QVBoxLayout(g)
        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setFont(QFont("Monospace", 9))
        self.te_log.setMinimumHeight(160)
        v.addWidget(self.te_log)
        return g

    # ── Slots ──────────────────────────────────────────────────────────────────

    def _on_mode_changed(self, mode: str):
        if mode == "User Gallery":
            self.le_target.setPlaceholderText("Handle whose gallery to download")
        else:
            self.le_target.setPlaceholderText("Leave blank to use your own account")

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self.le_output.text()
        )
        if path:
            self.le_output.setText(path)

    def _load_saved_credentials(self):
        cfg = bsky.load_config()
        if cfg.has_option("credentials", "handle"):
            self.le_handle.setText(cfg.get("credentials", "handle"))
        if cfg.has_option("credentials", "app_password"):
            self.le_pass.setText(cfg.get("credentials", "app_password"))

    def _append_log(self, msg: str):
        self.te_log.append(msg)
        sb = self.te_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _start(self):
        handle   = self.le_handle.text().strip()
        password = self.le_pass.text().strip()
        if not handle or not password:
            self._append_log("⚠  Handle and app password are required.")
            return

        bsky.save_config(handle, password)

        cfg = {
            "handle":   handle,
            "password": password,
            "mode":     self.cb_mode.currentText(),
            "target":   self.le_target.text().strip(),
            "media":    self.cb_media.currentText(),
            "pages":    self.sp_pages.value(),
            "output":   self.le_output.text().strip(),
        }

        self.te_log.clear()
        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.statusbar.showMessage("Downloading…")

        self.worker = DownloadWorker(cfg)
        self.worker.log.connect(self._append_log)
        self.worker.done.connect(self._on_done)
        self.worker.start()

    def _cancel(self):
        if self.worker:
            self.worker.cancel()
        self.btn_cancel.setEnabled(False)
        self.statusbar.showMessage("Cancelling…")

    def _on_done(self, ok: bool, msg: str):
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self._append_log(msg)
        self.statusbar.showMessage(msg)


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("BlueSky Downloader")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

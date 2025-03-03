# menu/sync_actions.py
import os
import io
import hashlib
import threading
import time
import json  # Import json module
from PySide6.QtWidgets import QMenu, QMessageBox, QDialog, QVBoxLayout, QLabel, QLineEdit
from PySide6.QtWidgets import QDialogButtonBox, QFormLayout, QCheckBox, QComboBox, QProgressBar
from PySide6.QtWidgets import QListWidget, QPushButton, QHBoxLayout, QWidget, QFileDialog
from PySide6.QtCore import Qt, Signal, QObject

# Google Drive imports
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    from google.oauth2 import service_account
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False

class WorkerSignals(QObject):
    """Signals for worker thread communication."""
    progress = Signal(int)
    finished = Signal()
    error = Signal(str)
    file_status = Signal(str)

class DriveSync:
    """Google Drive synchronization functionality."""

    def __init__(self):
        # Configuration
        # self.SERVICE_ACCOUNT_FILE = os.path.join('credentials', 'credentials.json') # Removed hardcoded path
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        self.DRIVE_FOLDER_ID = '1ZqSLWL7POqp0gufYuMxFdyHX0sjDKMtJ'  # Default folder ID
        self.LOCAL_DIR = 'data'  # Default local directory
        self.drive_service = None

    def authenticate(self, service_account_file): # Added service_account_file argument
        """Authenticate with Google Drive."""
        if not os.path.exists(service_account_file): # Use argument path
            raise FileNotFoundError(f"Credentials file not found at {service_account_file}")

        try:
            creds = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=self.SCOPES)
            self.drive_service = build('drive', 'v3', credentials=creds)
            return True
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def get_remote_file(self, file_name, folder_id):
        """
        Returns remote file metadata (including MD5 checksum) for a given file name in the specified folder.
        If the file does not exist remotely, returns None.
        """
        query = f"name = '{file_name}' and '{folder_id}' in parents and trashed = false"
        results = self.drive_service.files().list(
            q=query, fields="files(id, name, md5Checksum)").execute()
        items = results.get('files', [])
        return items[0] if items else None

    def get_remote_files(self, folder_id):
        """
        Lists all files in the specified Google Drive folder.
        Returns a list of file metadata including id, name, and MD5 checksum.
        """
        query = f"'{folder_id}' in parents and trashed = false"
        results = self.drive_service.files().list(
            q=query, fields="files(id, name, md5Checksum)").execute()
        return results.get('files', [])

    def get_local_md5(self, file_path):
        """
        Computes the MD5 hash for the local file.
        """
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()

    def upload_file(self, local_file_path, folder_id, signals=None):
        """
        Uploads a new file or updates an existing one on Google Drive.
        """
        file_name = os.path.basename(local_file_path)
        remote_file = self.get_remote_file(file_name, folder_id)

        if signals:
            signals.file_status.emit(f"Processing: {file_name}")

        try:
            media = MediaFileUpload(local_file_path, resumable=True)
            if remote_file:
                if signals:
                    signals.file_status.emit(f"Updating: {file_name}")
                file = self.drive_service.files().update(
                    fileId=remote_file['id'], media_body=media).execute()
            else:
                if signals:
                    signals.file_status.emit(f"Uploading: {file_name}")
                file_metadata = {'name': file_name, 'parents': [folder_id]}
                file = self.drive_service.files().create(
                    body=file_metadata, media_body=media, fields='id').execute()

            if signals:
                signals.file_status.emit(f"Completed: {file_name}")
            return True
        except Exception as e:
            if signals:
                signals.error.emit(f"Error with {file_name}: {str(e)}")
            return False

    def download_file(self, remote_file, local_file_path, signals=None):
        """
        Downloads a file from Google Drive and writes it to the local path.
        """
        file_name = os.path.basename(local_file_path)
        if signals:
            signals.file_status.emit(f"Downloading: {file_name}")

        try:
            request = self.drive_service.files().get_media(fileId=remote_file['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False

            while not done:
                status, done = downloader.next_chunk()
                if signals:
                    signals.progress.emit(int(status.progress() * 100))

            # Ensure directory exists
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            with open(local_file_path, "wb") as f:
                f.write(fh.getvalue())

            if signals:
                signals.file_status.emit(f"Completed: {file_name}")
            return True
        except Exception as e:
            if signals:
                signals.error.emit(f"Error with {file_name}: {str(e)}")
            return False

    def get_sync_status(self, local_dir, folder_id):
        """
        Get comprehensive sync status between local and remote files.
        Returns:
        - files_to_upload: Files that exist locally and need to be uploaded or updated
        - files_to_download: Files that exist remotely but not locally or have different content
        """
        files_to_upload = []
        files_to_download = []

        # Ensure local directory exists
        if not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)

        # Get all remote files
        remote_files = self.get_remote_files(folder_id)
        remote_files_dict = {file['name']: file for file in remote_files}

        # Check local files against remote
        local_files = [f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f))]
        for file_name in local_files:
            local_file_path = os.path.join(local_dir, file_name)
            local_md5 = self.get_local_md5(local_file_path)

            if file_name in remote_files_dict:
                # File exists both locally and remotely
                remote_md5 = remote_files_dict[file_name].get('md5Checksum', '')
                if local_md5 != remote_md5:
                    # Content differs, needs update
                    files_to_upload.append((file_name, remote_files_dict[file_name]))
            else:
                # File exists locally but not remotely
                files_to_upload.append((file_name, None))

        # Check remote files not found locally
        for file_name, remote_file in remote_files_dict.items():
            local_file_path = os.path.join(local_dir, file_name)

            if not os.path.exists(local_file_path):
                # File exists remotely but not locally
                files_to_download.append((file_name, remote_file))
            else:
                # Already processed above for upload check,
                # but might need download if remote is newer
                local_md5 = self.get_local_md5(local_file_path)
                remote_md5 = remote_file.get('md5Checksum', '')

                if local_md5 != remote_md5 and (file_name, remote_file) not in files_to_upload:
                    files_to_download.append((file_name, remote_file))

        return files_to_upload, files_to_download


class SyncActions:
    def __init__(self, main_window):
        self.main_window = main_window
        self.sync_menu = QMenu("Sync", self.main_window)
        self.drive_sync = DriveSync()
        self.settings_file = os.path.join('data', 'sync.json')
        self._load_settings() # Load settings from json file first
        self.create_actions()

    def _load_settings(self):
        """Load settings from sync.json file, or use defaults if file not found or invalid."""
        default_settings = {
            'server_url': "https://fintrack-cloud.example.com",
            'username': "",
            'api_key': "",
            'auto_sync': False,
            'sync_interval': "Daily",
            'conflict_resolution': "Always ask",
            'drive_folder_id': self.drive_sync.DRIVE_FOLDER_ID,
            'local_dir': self.drive_sync.LOCAL_DIR,
            'credentials_file': os.path.join('credentials', 'credentials.json') # Default credentials path
        }
        self.settings = default_settings
        data_dir = os.path.dirname(self.settings_file)
        os.makedirs(data_dir, exist_ok=True) # Ensure data directory exists

        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    # Update default settings with loaded values, keeping defaults for missing keys
                    self.settings.update(loaded_settings)
            except (FileNotFoundError, json.JSONDecodeError):
                print("Error loading settings from sync.json, using default settings.")
        else:
            print("sync.json not found, using default settings.")
        # Ensure DriveSync is updated with loaded settings (only folder and local dir for now, authentication is handled later)
        self.drive_sync.DRIVE_FOLDER_ID = self.settings['drive_folder_id']
        self.drive_sync.LOCAL_DIR = self.settings['local_dir']


    def _save_settings(self, dialog, settings):
        """Save the sync settings to sync.json."""
        # Simple validation
        if not settings['drive_folder_id'] or not settings['local_dir'] or not settings['credentials_file']: # Added credentials_file validation
            QMessageBox.warning(dialog, "Validation Error",
                              "Google Drive Folder ID, Credentials File and Local Directory are required fields.")
            return

        # Update settings
        self.settings = settings
        self.drive_sync.DRIVE_FOLDER_ID = settings['drive_folder_id']
        self.drive_sync.LOCAL_DIR = settings['local_dir']

        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4) # Save with indentation for readability
            QMessageBox.information(dialog, "Settings Saved", "Your synchronization settings have been saved successfully.")
            dialog.accept()
        except IOError as e:
            QMessageBox.critical(dialog, "Settings Error", f"Failed to save settings: {e}")


    def create_actions(self):
        # Upload submenu
        self.upload_action = self.sync_menu.addAction("Upload Data to Drive")
        self.upload_action.triggered.connect(self.upload_data)

        # Download submenu
        self.download_action = self.sync_menu.addAction("Download Data from Drive")
        self.download_action.triggered.connect(self.download_data)

        # Settings submenu
        self.settings_action = self.sync_menu.addAction("Sync Settings")
        self.settings_action.triggered.connect(self.sync_settings)

        # Separator
        self.sync_menu.addSeparator()

        # Check sync status
        self.check_sync_action = self.sync_menu.addAction("Check Sync Status")
        self.check_sync_action.triggered.connect(self.check_sync_status)

        # Update menu items based on Google Drive availability
        self.update_action = self.sync_menu.aboutToShow.connect(self.update_menu_state)

    def update_menu_state(self):
        """Update menu items based on Google Drive availability"""
        google_available = GOOGLE_DRIVE_AVAILABLE
        self.upload_action.setEnabled(google_available)
        self.download_action.setEnabled(google_available)
        self.check_sync_action.setEnabled(google_available)

    def _authenticate_drive(self):
        """Authenticate Google Drive using the configured credentials file."""
        if not self.drive_sync.authenticate(self.settings['credentials_file']): # Pass credentials file path
            QMessageBox.critical(self.main_window, "Authentication Error",
                               "Failed to authenticate with Google Drive. Please check your credentials file path in settings.")
            return False
        return True


    def upload_data(self):
        """Handle data upload to Google Drive"""
        if not GOOGLE_DRIVE_AVAILABLE:
            QMessageBox.warning(self.main_window, "Google Drive Not Available",
                              "Google Drive API is not available. Please install required packages.")
            return

        if not self._authenticate_drive(): # Use authentication method
            return

        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Upload Data to Google Drive")
        layout = QVBoxLayout()

        # Information label
        info_label = QLabel("Upload your financial data to Google Drive.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Directory selection
        dir_layout = QHBoxLayout()
        dir_label = QLabel(f"Local Directory: {self.settings['local_dir']}")
        dir_button = QPushButton("Change...")
        dir_button.clicked.connect(lambda: self._select_directory(dir_label))
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(dir_button)
        layout.addLayout(dir_layout)

        # Status label
        status_label = QLabel("Checking for files to upload...")
        layout.addWidget(status_label)

        # Files list
        files_list = QListWidget()
        layout.addWidget(files_list)

        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        layout.addWidget(progress_bar)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Upload")
        button_box.accepted.connect(lambda: self._perform_upload(
            dialog, progress_bar, status_label, files_list))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Check for files to upload
        self._update_upload_files_list(files_list, status_label)

        dialog.setLayout(layout)
        dialog.resize(500, 400)
        dialog.exec()

    def _select_directory(self, label_widget):
        """Select a local directory for data syncing."""
        directory = QFileDialog.getExistingDirectory(
            self.main_window, "Select Directory", self.settings['local_dir'])
        if directory:
            self.settings['local_dir'] = directory
            self.drive_sync.LOCAL_DIR = directory
            label_widget.setText(f"Local Directory: {directory}")

    def _update_upload_files_list(self, files_list, status_label):
        """Update the list of files to upload."""
        try:
            # Get files to upload
            files_to_upload, _ = self.drive_sync.get_sync_status(
                self.settings['local_dir'], self.settings['drive_folder_id'])

            files_list.clear()
            if files_to_upload:
                for file, remote in files_to_upload:
                    if remote:
                        files_list.addItem(f"{file} (update)")
                    else:
                        files_list.addItem(f"{file} (new)")
                status_label.setText(f"Found {len(files_to_upload)} files to upload")
            else:
                status_label.setText("No files to upload - all local files are in sync")
        except Exception as e:
            status_label.setText(f"Error: {str(e)}")

    def _perform_upload(self, dialog, progress_bar, status_label, files_list):
        """Perform the upload operation in a background thread."""
        # Get the files to upload
        files_to_upload, _ = self.drive_sync.get_sync_status(
            self.settings['local_dir'], self.settings['drive_folder_id'])

        if not files_to_upload:
            QMessageBox.information(dialog, "No Changes", "No files need to be uploaded.")
            dialog.accept()
            return

        # Create signals for thread communication
        signals = WorkerSignals()
        signals.progress.connect(progress_bar.setValue)
        signals.file_status.connect(status_label.setText)
        signals.finished.connect(lambda: self._upload_finished(dialog))
        signals.error.connect(lambda msg: QMessageBox.warning(dialog, "Upload Error", msg))

        # Start upload thread
        total_files = len(files_to_upload)

        def upload_thread_func():
            successful = 0
            for i, (file, _) in enumerate(files_to_upload):
                local_file_path = os.path.join(self.settings['local_dir'], file)
                signals.progress.emit(int((i / total_files) * 100))
                if self.drive_sync.upload_file(local_file_path, self.settings['drive_folder_id'], signals):
                    successful += 1
            signals.progress.emit(100)
            signals.file_status.emit(f"Upload completed: {successful}/{total_files} files uploaded")
            signals.finished.emit()

        thread = threading.Thread(target=upload_thread_func)
        thread.daemon = True
        thread.start()

    def _upload_finished(self, dialog):
        """Handle upload completion."""
        QMessageBox.information(dialog, "Upload Complete", "Your files have been uploaded to Google Drive.")
        dialog.accept()

    def download_data(self):
        """Handle data download from Google Drive"""
        if not GOOGLE_DRIVE_AVAILABLE:
            QMessageBox.warning(self.main_window, "Google Drive Not Available",
                              "Google Drive API is not available. Please install required packages.")
            return

        if not self._authenticate_drive(): # Use authentication method
            return

        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Download Data from Google Drive")
        layout = QVBoxLayout()

        # Information label
        info_label = QLabel("Download your financial data from Google Drive.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Directory selection
        dir_layout = QHBoxLayout()
        dir_label = QLabel(f"Local Directory: {self.settings['local_dir']}")
        dir_button = QPushButton("Change...")
        dir_button.clicked.connect(lambda: self._select_directory(dir_label))
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(dir_button)
        layout.addLayout(dir_layout)

        # Status label
        status_label = QLabel("Checking for files to download...")
        layout.addWidget(status_label)

        # Files list
        files_list = QListWidget()
        layout.addWidget(files_list)

        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        layout.addWidget(progress_bar)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Download")
        button_box.accepted.connect(lambda: self._perform_download(
            dialog, progress_bar, status_label, files_list))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Check for files to download
        self._update_download_files_list(files_list, status_label)

        dialog.setLayout(layout)
        dialog.resize(500, 400)
        dialog.exec()

    def _update_download_files_list(self, files_list, status_label):
        """Update the list of files to download."""
        try:
            # Get files to download
            _, files_to_download = self.drive_sync.get_sync_status(
                self.settings['local_dir'], self.settings['drive_folder_id'])

            files_list.clear()
            if files_to_download:
                for file, remote in files_to_download:
                    if os.path.exists(os.path.join(self.settings['local_dir'], file)):
                        files_list.addItem(f"{file} (update)")
                    else:
                        files_list.addItem(f"{file} (new)")
                status_label.setText(f"Found {len(files_to_download)} files to download")
            else:
                status_label.setText("No files to download - all remote files are in sync")
        except Exception as e:
            status_label.setText(f"Error: {str(e)}")

    def _perform_download(self, dialog, progress_bar, status_label, files_list):
        """Perform the download operation in a background thread."""
        # Get the files to download
        _, files_to_download = self.drive_sync.get_sync_status(
            self.settings['local_dir'], self.settings['drive_folder_id'])

        if not files_to_download:
            QMessageBox.information(dialog, "No Changes", "No files need to be downloaded.")
            dialog.accept()
            return

        # Create signals for thread communication
        signals = WorkerSignals()
        signals.progress.connect(progress_bar.setValue)
        signals.file_status.connect(status_label.setText)
        signals.finished.connect(lambda: self._download_finished(dialog))
        signals.error.connect(lambda msg: QMessageBox.warning(dialog, "Download Error", msg))

        # Start download thread
        total_files = len(files_to_download)

        def download_thread_func():
            successful = 0
            for i, (file, remote) in enumerate(files_to_download):
                local_file_path = os.path.join(self.settings['local_dir'], file)
                signals.progress.emit(int((i / total_files) * 100))
                if self.drive_sync.download_file(remote, local_file_path, signals):
                    successful += 1
            signals.progress.emit(100)
            signals.file_status.emit(f"Download completed: {successful}/{total_files} files downloaded")
            signals.finished.emit()

        thread = threading.Thread(target=download_thread_func)
        thread.daemon = True
        thread.start()

    def _download_finished(self, dialog):
        """Handle download completion."""
        QMessageBox.information(dialog, "Download Complete", "Your files have been downloaded from Google Drive.")
        dialog.accept()

    def check_sync_status(self):
        """Check synchronization status between local files and Google Drive"""
        if not GOOGLE_DRIVE_AVAILABLE:
            QMessageBox.warning(self.main_window, "Google Drive Not Available",
                              "Google Drive API is not available. Please install required packages.")
            return

        if not self._authenticate_drive(): # Use authentication method
            return

        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Sync Status")
        layout = QVBoxLayout()

        # Status label
        status_label = QLabel("Checking sync status...")
        layout.addWidget(status_label)

        # Create tabs for upload and download
        tab_layout = QVBoxLayout()

        # Upload section
        upload_label = QLabel("<b>Files to Upload (Local → Drive):</b>")
        tab_layout.addWidget(upload_label)

        upload_list = QListWidget()
        tab_layout.addWidget(upload_list)

        # Download section
        download_label = QLabel("<b>Files to Download (Drive → Local):</b>")
        tab_layout.addWidget(download_label)

        download_list = QListWidget()
        tab_layout.addWidget(download_list)

        layout.addLayout(tab_layout)

        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(lambda: self._update_sync_status(
            upload_list, download_list, status_label))
        layout.addWidget(refresh_button)

        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Check for sync status
        self._update_sync_status(upload_list, download_list, status_label)

        dialog.setLayout(layout)
        dialog.resize(500, 500)
        dialog.exec()

    def _update_sync_status(self, upload_list, download_list, status_label):
        """Update the sync status lists."""
        status_label.setText("Checking sync status...")

        try:
            # Get sync status
            files_to_upload, files_to_download = self.drive_sync.get_sync_status(
                self.settings['local_dir'], self.settings['drive_folder_id'])

            # Update upload list
            upload_list.clear()
            if files_to_upload:
                for file, remote in files_to_upload:
                    if remote:
                        upload_list.addItem(f"{file} (update)")
                    else:
                        upload_list.addItem(f"{file} (new)")
            else:
                upload_list.addItem("No files need to be uploaded")

            # Update download list
            download_list.clear()
            if files_to_download:
                for file, remote in files_to_download:
                    if os.path.exists(os.path.join(self.settings['local_dir'], file)):
                        download_list.addItem(f"{file} (update)")
                    else:
                        download_list.addItem(f"{file} (new)")
            else:
                download_list.addItem("No files need to be downloaded")

            # Update status
            total_changes = len(files_to_upload) + len(files_to_download)
            if total_changes > 0:
                status_label.setText(f"Found {total_changes} files that need synchronization")
            else:
                status_label.setText("All files are in sync")

        except Exception as e:
            status_label.setText(f"Error: {str(e)}")

    def sync_settings(self):
        """Handle sync settings configuration"""
        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Sync Settings")
        layout = QVBoxLayout()

        # Information label
        info_label = QLabel("Configure your synchronization settings.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Form layout for settings
        form_layout = QFormLayout()

        # Google Drive settings
        drive_section_label = QLabel("<b>Google Drive Settings</b>")
        form_layout.addRow(drive_section_label)

        folder_id = QLineEdit(self.settings['drive_folder_id'])
        form_layout.addRow("Folder ID:", folder_id)

        # Credentials File selection  <- New Section
        cred_file_layout = QHBoxLayout()
        credentials_file = QLineEdit(self.settings['credentials_file'])
        cred_button = QPushButton("Browse...")
        cred_button.clicked.connect(lambda: self._browse_credentials_file(credentials_file)) # New browse function
        cred_file_layout.addWidget(credentials_file)
        cred_file_layout.addWidget(cred_button)
        form_layout.addRow("Credentials File:", cred_file_layout)


        # Directory selection
        dir_layout = QHBoxLayout()
        local_dir = QLineEdit(self.settings['local_dir'])
        dir_button = QPushButton("Browse...")
        dir_button.clicked.connect(lambda: self._browse_directory(local_dir))
        dir_layout.addWidget(local_dir)
        dir_layout.addWidget(dir_button)
        form_layout.addRow("Local Directory:", dir_layout)

        # Legacy server settings section
        server_section_label = QLabel("<b>Legacy Server Settings</b>")
        form_layout.addRow(server_section_label)

        server_url = QLineEdit(self.settings['server_url'])
        form_layout.addRow("Server URL:", server_url)

        username = QLineEdit(self.settings['username'])
        form_layout.addRow("Username:", username)

        api_key = QLineEdit(self.settings['api_key'])
        api_key.setEchoMode(QLineEdit.Password)
        form_layout.addRow("API Key:", api_key)

        # Auto sync settings
        sync_section_label = QLabel("<b>Synchronization Options</b>")
        form_layout.addRow(sync_section_label)

        auto_sync = QCheckBox("Enable automatic synchronization")
        auto_sync.setChecked(self.settings['auto_sync'])
        form_layout.addRow("Auto-Sync:", auto_sync)

        sync_interval = QComboBox()
        sync_interval.addItems(["Every hour", "Every 4 hours", "Every 12 hours", "Daily", "Weekly"])
        sync_interval.setCurrentText(self.settings['sync_interval'])
        form_layout.addRow("Sync Interval:", sync_interval)

        # Conflict resolution
        conflict_resolution = QComboBox()
        conflict_resolution.addItems(["Always ask", "Remote wins", "Local wins"])
        conflict_resolution.setCurrentText(self.settings['conflict_resolution'])
        form_layout.addRow("Conflict Resolution:", conflict_resolution)

        layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self._save_settings(dialog, {
            'server_url': server_url.text(),
            'username': username.text(),
            'api_key': api_key.text(),
            'auto_sync': auto_sync.isChecked(),
            'sync_interval': sync_interval.currentText(),
            'conflict_resolution': conflict_resolution.currentText(),
            'drive_folder_id': folder_id.text(),
            'local_dir': local_dir.text(),
            'credentials_file': credentials_file.text() # Get credentials file path
        }))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        dialog.resize(500, 500)
        dialog.exec()

    def _browse_directory(self, line_edit):
        """Open directory browser and update the line edit with selected path."""
        directory = QFileDialog.getExistingDirectory(
            self.main_window, "Select Directory", line_edit.text())
        if directory:
            line_edit.setText(directory)

    def _browse_credentials_file(self, line_edit):
        """Open file browser for credentials.json and update the line edit."""
        file_path, _ = QFileDialog.getOpenFileName( # getOpenFileName instead of getExistingDirectory
            self.main_window, "Select Credentials File", line_edit.text(), "JSON Files (*.json)") # File filter
        if file_path:
            line_edit.setText(file_path)
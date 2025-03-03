# backup_system.py
import os
import zipfile
import datetime
import shutil
from pathlib import Path

class BackupSystem:
    def __init__(self, parent=None, backup_dir="backups", data_dir="data", max_backups=20):
        """
        Initialize the backup system.
        
        Args:
            parent: The parent window (optional)
            backup_dir: Directory to store backups
            data_dir: Directory to backup
            max_backups: Maximum number of backup files to keep
        """
        self.parent = parent
        self.backup_dir = backup_dir
        self.data_dir = data_dir
        self.max_backups = max_backups
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self):
        """Create a zip backup of the data directory."""
        try:
            # Generate timestamped filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"fintrack_backup_{timestamp}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Create zip file
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                data_path = Path(self.data_dir)
                
                # Check if data directory exists
                if not data_path.exists():
                    print(f"Warning: Data directory '{self.data_dir}' not found. Backup skipped.")
                    return False
                
                # Add all files in data directory to zip
                for file_path in data_path.rglob('*'):
                    if file_path.is_file():
                        # Store the relative path in the zip
                        zipf.write(
                            file_path, 
                            arcname=str(file_path.relative_to(data_path.parent))
                        )
            
            # Manage backup rotation (keep only max_backups)
            self._cleanup_old_backups()
            
            print(f"Backup created successfully: {backup_path}")
            return True
            
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            return False
    
    def _cleanup_old_backups(self):
        """Remove old backups if we exceed the maximum number allowed."""
        try:
            # Get list of backup files sorted by creation time (oldest first)
            backup_files = []
            for f in os.listdir(self.backup_dir):
                if f.startswith("fintrack_backup_") and f.endswith(".zip"):
                    full_path = os.path.join(self.backup_dir, f)
                    if os.path.isfile(full_path):
                        creation_time = os.path.getctime(full_path)
                        backup_files.append((full_path, creation_time))
            
            # Sort by creation time (oldest first)
            backup_files.sort(key=lambda x: x[1])
            
            # Remove oldest backups if we have too many
            while len(backup_files) > self.max_backups:
                oldest_file = backup_files[0][0]
                os.remove(oldest_file)
                print(f"Removed old backup: {oldest_file}")
                backup_files.pop(0)
                
        except Exception as e:
            print(f"Error cleaning up old backups: {str(e)}")

def register_app_close_backup(app, window):
    """
    Register a function to create a backup when the application closes.
    
    Args:
        app: QApplication instance
        window: MainWindow instance
    """
    backup_system = BackupSystem()
    
    # Store original closeEvent
    original_close_event = window.closeEvent
    
    # Define new closeEvent that creates backup before closing
    def closeEvent_with_backup(event):
        print("Application closing, creating backup...")
        backup_system.create_backup()
        # Call the original closeEvent
        original_close_event(event)
    
    # Replace the closeEvent method
    window.closeEvent = closeEvent_with_backup
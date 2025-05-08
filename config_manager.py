import json
import os
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.config_file = Path(__file__).parent / 'config.json'
        self.config = self._load_config()

    def _load_config(self):
        """Load configuration from file or create default if not exists."""
        if not self.config_file.exists():
            default_config = {
                'import': {
                    'default_destination': '',
                    'max_threads': 4,
                    'skip_existing': True,
                    'copy_xmp_files': True,
                    'file_organization': {
                        'date_format': '%Y-%m-%d',
                        'add_sequence_number': True
                    }
                },
                'sorter': {
                    'stack_interval': 1.0,
                    'min_stack_size': 2,
                    'stack_name_format': 'Stack_{:03d}',
                    'progress_update_count': 20,
                    'exiftool': {
                        'date_format': '%Y:%m:%d %H:%M:%S',
                        'exif_tag': 'DateTimeOriginal'
                    }
                },
                'helicon_focus': {
                    'radius': 3,
                    'smoothing': 1,
                    'jpeg_quality': 95,
                    'output_format': 'dng',
                    'helicon_path': '/Applications/HeliconFocus.app/Contents/MacOS/HeliconFocus',
                    'methods': {
                        'A': True,
                        'B': True,
                        'C': False,
                        'AB': True
                    }
                }
            }
            self._save_config(default_config)
            return default_config
        
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def _save_config(self, config):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

    def get_config(self):
        """Get the complete configuration."""
        return self.config

    def get_default_destination(self):
        """Get the default destination path."""
        return self.config.get('import', {}).get('default_destination', '')

    def set_default_destination(self, path):
        """Set the default destination path."""
        if 'import' not in self.config:
            self.config['import'] = {}
        self.config['import']['default_destination'] = str(Path(path).absolute())
        self._save_config(self.config)

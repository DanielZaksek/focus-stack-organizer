"""
HeliconFocus integration module for focus stacking.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import subprocess
import time
from typing import List, Optional, Dict, Any

from config_manager import ConfigManager


class Method(Enum):
    """HeliconFocus stacking methods.
    
    Available methods:
        A (0): Method A - Better for sharp edges
        B (1): Method B - Better for smooth transitions
        C (2): Method C - Combination of A and B characteristics
    """
    A = 0  # Better for sharp edges
    B = 1  # Better for smooth transitions
    C = 2  # Combination of A and B


@dataclass
class HeliconConfig:
    """HeliconFocus configuration parameters.
    
    Args:
        radius: Radius parameter for HeliconFocus (1-8). Higher values include more
            distant areas when calculating the depth map.
        smoothing: Smoothing parameter for HeliconFocus (0-4). Higher values reduce
            noise but may also reduce sharpness.
        jpeg_quality: JPEG quality if output_format is 'jpg' (1-100)
        output_format: Output format ('jpg', 'tif', or 'dng'). DNG preserves the most
            information but results in larger files.
        methods: Dictionary of enabled stacking methods. Keys are method names ('A', 'B',
            'C', 'AB'), values are boolean flags.
        helicon_path: Path to HeliconFocus executable
    """
    radius: int = 3
    smoothing: int = 1
    jpeg_quality: int = 95
    output_format: str = 'dng'
    methods: Dict[str, bool] = None
    helicon_path: str = '/Applications/HeliconFocus.app/Contents/MacOS/HeliconFocus'
    
    @property
    def enabled_methods(self) -> List[Method]:
        """Get list of enabled basic methods (A, B, C)."""
        if not self.methods:
            return []
        return [Method[name] for name, enabled in self.methods.items()
                if enabled and name in ('A', 'B', 'C')]
    
    def __post_init__(self):
        """Initialize default values and validate configuration."""
        if self.methods is None:
            self.methods = {
                'A': True,
                'B': True,
                'C': False,
                'AB': True
            }
        
        if not 1 <= self.radius <= 8:
            raise ValueError("Radius must be between 1 and 8")
        if not 0 <= self.smoothing <= 4:
            raise ValueError("Smoothing must be between 0 and 4")
        if not 1 <= self.jpeg_quality <= 100:
            raise ValueError("JPEG quality must be between 1 and 100")
        if self.output_format not in ["jpg", "tif", "dng"]:
            raise ValueError("Output format must be 'jpg', 'tif', or 'dng'")
        if not Path(self.helicon_path).exists():
            raise FileNotFoundError(f"HeliconFocus not found at {self.helicon_path}")
    
    @classmethod
    def from_config(cls) -> 'HeliconConfig':
        """Create HeliconConfig from config.json settings."""
        config = ConfigManager().get_config()
        helicon_config = config.get('helicon_focus', {})
        
        return cls(
            radius=helicon_config.get('radius', 3),
            smoothing=helicon_config.get('smoothing', 1),
            jpeg_quality=helicon_config.get('jpeg_quality', 95),
            output_format=helicon_config.get('output_format', 'dng'),
            methods=helicon_config.get('methods', None),
            helicon_path=helicon_config.get('helicon_path', 
                '/Applications/HeliconFocus.app/Contents/MacOS/HeliconFocus')
        )
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if not 1 <= self.radius <= 8:
            raise ValueError("Radius must be between 1 and 8")
        if not 0 <= self.smoothing <= 4:
            raise ValueError("Smoothing must be between 0 and 4")
        if not 1 <= self.jpeg_quality <= 100:
            raise ValueError("JPEG quality must be between 1 and 100")
        if self.output_format not in ["jpg", "tif", "dng"]:
            raise ValueError("Output format must be 'jpg', 'tif', or 'dng'")
        if not Path(self.helicon_path).exists():
            raise FileNotFoundError(f"HeliconFocus not found at {self.helicon_path}")


def create_input_file(stack_dir: Path, supported_extensions: List[str]) -> Optional[Path]:
    """Create input file listing all images to process.
    
    Args:
        stack_dir: Directory containing the image files
        supported_extensions: List of supported file extensions (e.g., ['.orf', '.RAF'])
    
    Returns:
        Path to created input file or None if no images found
    """
    input_file = stack_dir / "input.txt"
    
    # Build pattern for supported formats
    patterns = [f"*.{ext[1:]}" for ext in supported_extensions]
    patterns.extend([f"*.{ext[1:].upper()}" for ext in supported_extensions])
    format_pattern = ' '.join(patterns)
    
    try:
        cmd = f"cd {stack_dir.absolute()} && (ls {format_pattern} 2>/dev/null || true) | "\
              f"sed 's|^|{stack_dir.absolute()}/|' > {input_file.absolute()}"
        subprocess.run(cmd, shell=True, check=True)
        
        # Check if any files were found
        if input_file.stat().st_size == 0:
            print(f"⚠️ No supported image files found in {stack_dir}")
            return None
        return input_file
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create input file: {e}")
        return None


def run_helicon_focus(cmd: List[str], description: str) -> bool:
    """Run HeliconFocus with given command.
    
    Args:
        cmd: Command line arguments for HeliconFocus
        description: Description of the operation for logging
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\n📦 {description}...")
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            elapsed = time.time() - start_time
            print(f"✅ Completed successfully in {elapsed:.2f} seconds")
            return True
        else:
            print(f"❌ Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Failed to run HeliconFocus: {e}")
        return False


def process_stack(
    stack_dir: Path,
    output_dir: Path,
    config: Optional[HeliconConfig] = None
) -> List[Path]:
    """Process a stack with Helicon Focus using methods A, B, C.
    
    This function processes a stack of images using different HeliconFocus methods.
    It checks for existing results and only processes missing methods. If combine_ab
    is True, it will also create an A+B combination using method B.
    
    Args:
        stack_dir (Path): Directory containing stack images
        output_dir (Path): Directory for output images
        radius (int, optional): Radius parameter for HeliconFocus. Defaults to 3.
        smoothing (int, optional): Smoothing parameter for HeliconFocus. Defaults to 1.
        jpeg_quality (int, optional): JPEG quality (1-100). Defaults to 95.
        output_format (str, optional): Output format (jpg, tif or dng). Defaults to 'dng'.
        helicon_path (str, optional): Path to HeliconFocus executable.
        combine_ab (bool, optional): Whether to combine methods A and B. Defaults to True.
    
    Returns:
        List[Path]: List of output files generated by HeliconFocus.
    
    Note:
        The function creates a HeliconConfig object internally to manage configuration
        parameters. It uses the Method enum to handle different stacking methods.
    """
    print(f"\n💾 Starting HeliconFocus for {stack_dir.name}")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Import ImageFormat here to avoid circular imports
    from focus_stack_sorter import ImageFormat
    
    # Create input file with source images
    input_file = create_input_file(stack_dir, ImageFormat.all_extensions())
    if not input_file:
        return []
    
    # Use provided config or load from config.json
    if config is None:
        config = HeliconConfig.from_config()
    
    # Determine which methods to process
    method_map = {
        'A': Method.A,
        'B': Method.B,
        'C': Method.C
    }
    
    existing_methods = []
    missing_methods = []
    results = []
    
    # Check which output files already exist and which methods are enabled
    for method_name, enabled in config.methods.items():
        if method_name == 'AB':
            # Handle A+B combination separately
            continue
            
        if not enabled:
            # Skip disabled methods
            continue
            
        method = method_map[method_name]
        output_file = output_dir / f"{stack_dir.name}_{method.name}.{config.output_format}"
        
        if output_file.exists():
            existing_methods.append(method)
            results.append(output_file)
        else:
            missing_methods.append(method)
    
    if existing_methods:
        print(f"\n💡 Found existing results for methods: {', '.join(m.name for m in existing_methods)}")
        print(f"🔄 Will generate missing methods: {', '.join(m.name for m in missing_methods)}")
    
    # Process missing methods
    for method in missing_methods:
        output_file = output_dir / f"{stack_dir.name}_{method.name}.{config.output_format}"
        
        # Create command line for HeliconFocus
        cmd = [
            config.helicon_path,
            '-silent',
            '-i', str(input_file),
            f'-save:{output_file}',
            f'-mp:{method.value}',  # Method parameter (A=0, B=1, C=2)
            f'-rp:{config.radius}',  # Radius parameter
            f'-sp:{config.smoothing}'  # Smoothing parameter
        ]
        
        # Add JPEG quality only for JPG output
        if config.output_format.lower() == 'jpg':
            cmd.append(f'-j:{config.jpeg_quality}')
        
        if run_helicon_focus(cmd, f"Processing {stack_dir.name} with Method {method.name}"):
            results.append(output_file)
    
    # Process A+B combination if enabled
    if config.methods.get('AB', False):
        ab_file = output_dir / f"{stack_dir.name}_AB.{config.output_format}"
        if ab_file.exists():
            print("\n💡 A+B combination already exists")
            results.append(ab_file)
            return results
        
        # Check if both A and B methods are enabled and available
        all_methods = existing_methods + missing_methods
        if Method.A in all_methods and Method.B in all_methods and \
           config.methods.get('A', False) and config.methods.get('B', False):
            
            # Create input file for A+B combination
            a_file = output_dir / f"{stack_dir.name}_A.{config.output_format}"
            b_file = output_dir / f"{stack_dir.name}_B.{config.output_format}"
            ab_input = stack_dir / "input_ab.txt"
            
            try:
                with open(ab_input, 'w') as f:
                    f.write(f"{a_file.absolute()}\n{b_file.absolute()}\n")
                
                # Create command line for HeliconFocus
                cmd = [
                    config.helicon_path,
                    '-silent',
                    '-i', str(ab_input),
                    f'-save:{ab_file}',
                    '-mp:1',  # Method B for combination
                    f'-rp:{config.radius}',
                    f'-sp:{config.smoothing}'
                ]
                
                # Add JPEG quality only for JPG output
                if config.output_format.lower() == 'jpg':
                    cmd.append(f'-j:{config.jpeg_quality}')
                
                if run_helicon_focus(cmd, "Combining methods A and B"):
                    results.append(ab_file)
            finally:
                # Clean up AB input file
                try:
                    if ab_input.exists():
                        ab_input.unlink()
                except Exception:
                    pass
    
    # Clean up original input file
    try:
        input_file.unlink()
    except Exception:
        pass
    
    return results

"""
HeliconFocus integration module for focus stacking.
"""
from pathlib import Path
import subprocess
from typing import List

# HeliconFocus Configuration
HELICON_PATH = '/Applications/HeliconFocus.app/Contents/MacOS/HeliconFocus'
RADIUS = 3          # Radius parameter for HeliconFocus
SMOOTHING = 1       # Smoothing parameter for HeliconFocus
JPEG_QUALITY = 95   # JPEG quality (1-100)
OUTPUT_FORMAT = 'dng'  # Output format (jpg, tif or dng)

def process_stack(
    stack_dir: Path, 
    output_dir: Path, 
    radius: int = RADIUS,
    smoothing: int = SMOOTHING,
    jpeg_quality: int = JPEG_QUALITY,
    output_format: str = OUTPUT_FORMAT,
    helicon_path: str = HELICON_PATH
) -> List[Path]:
    """Process a stack with Helicon Focus using methods A, B, C.
    
    Args:
        stack_dir: Directory containing images to stack
        output_dir: Output directory for stacked images
        radius: Radius parameter (default: {RADIUS})
        smoothing: Smoothing parameter (default: {SMOOTHING})
        jpeg_quality: JPEG quality 1-100 (default: {JPEG_QUALITY})
        output_format: Output format 'jpg', 'tif' or 'dng' (default: {OUTPUT_FORMAT})
        helicon_path: Path to HeliconFocus executable (default: {HELICON_PATH})
    
    Returns:
        List of generated files
    """
    print(f"\n💾 Starting HeliconFocus for {stack_dir.name}")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create input.txt with list of source files
    input_file = stack_dir / "input.txt"
    try:
        # Create input.txt with absolute paths for all supported formats
        raw_formats = "*.ORF *.orf *.NEF *.nef *.CR2 *.cr2 *.ARW *.arw *.RW2 *.rw2 *.RAF *.raf *.DNG *.dng"
        standard_formats = "*.JPG *.jpg *.JPEG *.jpeg *.TIFF *.tiff *.TIF *.tif *.PNG *.png"
        
        # Build command to find all supported image files
        cmd = f"cd {stack_dir.absolute()} && (ls {raw_formats} {standard_formats} 2>/dev/null || true) | sed 's|^|{stack_dir.absolute()}/|' > {input_file.absolute()}"
        subprocess.run(
            cmd,
            shell=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create input file: {e}")
        return []
    
    # Process with different methods
    methods = {'A': 0, 'B': 1, 'C': 2}  # Method mapping (A=0, B=1, C=2)
    results = []
    
    for method_name, method_value in methods.items():
        output_file = output_dir / f"{stack_dir.name}_{method_name}.{output_format}"
        
        # Create command line for HeliconFocus
        cmd = [
            HELICON_PATH,
            '-silent',
            '-i', str(input_file),
            f'-save:{output_file}',
            f'-mp:{method_value}',  # Method parameter (A=0, B=1, C=2)
            f'-rp:{radius}',         # Radius parameter
            f'-sp:{smoothing}'       # Smoothing parameter
        ]
        
        # Add JPEG quality only for JPG output
        if output_format.lower() == 'jpg':
            cmd.append(f'-j:{jpeg_quality}')
        
        print(f"\n📦 Processing {stack_dir.name} with Method {method_name}...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                results.append(output_file)
                print(f"✅ Method {method_name} completed successfully")
            else:
                print(f"❌ Error with Method {method}: {result.stderr}")
        except Exception as e:
            print(f"❌ Failed to run HeliconFocus: {e}")
    
    # Combine A and B using method B
    if len(results) >= 2:
        a_file = output_dir / f"{stack_dir.name}_A.{output_format}"
        b_file = output_dir / f"{stack_dir.name}_B.{output_format}"
        
        if a_file.exists() and b_file.exists():
            # Create new input.txt for A+B combination
            ab_input = stack_dir / "input_ab.txt"
            with open(ab_input, 'w') as f:
                f.write(f"{a_file.absolute()}\n{b_file.absolute()}\n")
            
            ab_file = output_dir / f"{stack_dir.name}_AB.{output_format}"
            
            # Create command line for HeliconFocus
            cmd = [
                helicon_path,
                '-silent',
                '-i', str(ab_input),
                f'-save:{ab_file}',
                '-mp:1',           # Method B for combination
                f'-rp:{RADIUS}',
                f'-sp:{SMOOTHING}'
            ]
            
            # Add JPEG quality only for JPG output
            if OUTPUT_FORMAT.lower() == 'jpg':
                cmd.append(f'-j:{JPEG_QUALITY}')
            
            print("\n📦 Combining methods A and B...")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    results.append(ab_file)
                    print("✅ A+B combination completed successfully")
                else:
                    print(f"❌ Error combining A+B: {result.stderr}")
            except Exception as e:
                print(f"❌ Failed to combine A+B: {e}")
            
            # Clean up AB input file
            try:
                ab_input.unlink()
            except Exception:
                pass
    
    # Clean up original input file
    try:
        input_file.unlink()
    except Exception:
        pass
    
    return results

from pathlib import Path
import subprocess
from .pymol_templates import PYMOL_SCENE_TEMPLATE


def render_pymol_scene(complex_pdb: Path, out_dir: Path, basename: str, pymol_bin: str = "pymol") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    session_out = out_dir / f"{basename}.pse"
    png_out = out_dir / f"{basename}.png"
    script_text = PYMOL_SCENE_TEMPLATE.format(
        complex_pdb=str(complex_pdb),
        session_out=str(session_out),
        png_out=str(png_out),
    )
    script_file = out_dir / f"{basename}.pml"
    script_file.write_text(script_text, encoding="utf-8")
    try:
        subprocess.run([pymol_bin, "-cq", str(script_file)], check=True)
    except Exception as e:
        print(f"⚠️  PyMOL render failed for {basename}: {e}")
    return png_out



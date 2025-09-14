"""
PyMOL integration module for post-docking analysis pipeline.

This module handles 3D structure visualization, comparative scenes,
and interaction analysis using PyMOL.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import subprocess
import tempfile
import os

class PyMOLVisualizer:
    """
    PyMOL visualizer for creating 3D structure visualizations and comparative scenes.
    """
    
    def __init__(self, output_dir: Path):
        """
        Initialize PyMOL visualizer.
        
        Parameters
        ----------
        output_dir : Path
            Output directory for PyMOL files and images
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.pymol_commands = []
        
    def create_comparative_scene(self, reference_pdb: Path, novel_pdb: Path, 
                               highlight_residues: List[int] = None,
                               scene_name: str = "comparative_scene") -> Path:
        """
        Create a comparative scene between reference and novel compound structures.
        
        Parameters
        ----------
        reference_pdb : Path
            Path to reference structure PDB file
        novel_pdb : Path
            Path to novel compound structure PDB file
        highlight_residues : List[int], optional
            List of residue numbers to highlight
        scene_name : str
            Name for the scene
            
        Returns
        -------
        Path
            Path to the created PyMOL session file
        """
        print(f"🎬 Creating comparative scene: {scene_name}")
        
        # Generate PyMOL script
        pymol_script = self._generate_comparative_script(
            reference_pdb, novel_pdb, highlight_residues, scene_name
        )
        
        # Save script to file
        script_file = self.output_dir / f"{scene_name}_script.pml"
        with open(script_file, 'w') as f:
            f.write(pymol_script)
        
        # Execute PyMOL script
        self._execute_pymol_script(script_file)
        
        # Save session
        session_file = self.output_dir / f"{scene_name}.pse"
        self._save_pymol_session(session_file)
        
        print(f"✅ Comparative scene created: {session_file}")
        return session_file
    
    def create_interaction_analysis(self, pdb_file: Path, ligand_resname: str = "UNK",
                                  cutoff_distance: float = 4.0,
                                  scene_name: str = "interaction_analysis") -> Path:
        """
        Create detailed interaction analysis scene.
        
        Parameters
        ----------
        pdb_file : Path
            Path to PDB file
        ligand_resname : str
            Residue name of the ligand
        cutoff_distance : float
            Distance cutoff for interaction analysis (Å)
        scene_name : str
            Name for the scene
            
        Returns
        -------
        Path
            Path to the created PyMOL session file
        """
        print(f"🔬 Creating interaction analysis: {scene_name}")
        
        # Generate interaction analysis script
        pymol_script = self._generate_interaction_script(
            pdb_file, ligand_resname, cutoff_distance, scene_name
        )
        
        # Save script to file
        script_file = self.output_dir / f"{scene_name}_script.pml"
        with open(script_file, 'w') as f:
            f.write(pymol_script)
        
        # Execute PyMOL script
        self._execute_pymol_script(script_file)
        
        # Save session
        session_file = self.output_dir / f"{scene_name}.pse"
        self._save_pymol_session(session_file)
        
        print(f"✅ Interaction analysis created: {session_file}")
        return session_file
    
    def create_best_poses_gallery(self, pdb_files: List[Path], 
                                scene_name: str = "best_poses_gallery") -> Path:
        """
        Create a gallery of best poses for comparison.
        
        Parameters
        ----------
        pdb_files : List[Path]
            List of PDB files for best poses
        scene_name : str
            Name for the scene
            
        Returns
        -------
        Path
            Path to the created PyMOL session file
        """
        print(f"🖼️ Creating best poses gallery: {scene_name}")
        
        # Generate gallery script
        pymol_script = self._generate_gallery_script(pdb_files, scene_name)
        
        # Save script to file
        script_file = self.output_dir / f"{scene_name}_script.pml"
        with open(script_file, 'w') as f:
            f.write(pymol_script)
        
        # Execute PyMOL script
        self._execute_pymol_script(script_file)
        
        # Save session
        session_file = self.output_dir / f"{scene_name}.pse"
        self._save_pymol_session(session_file)
        
        print(f"✅ Best poses gallery created: {session_file}")
        return session_file
    
    def _generate_comparative_script(self, reference_pdb: Path, novel_pdb: Path,
                                   highlight_residues: List[int], scene_name: str) -> str:
        """Generate PyMOL script for comparative scene."""
        
        script = f"""
# PyMOL Script for Comparative Scene: {scene_name}
# Generated by PDB Prepare Wizard Post-Docking Analysis

# Clear workspace
cmd.delete("all")

# Load structures
cmd.load("{reference_pdb}", "reference")
cmd.load("{novel_pdb}", "novel")

# Basic visualization setup
cmd.show("cartoon", "all")
cmd.color("gray78", "all")
cmd.set("cartoon_transparency", 0.55)
cmd.set("cartoon_smooth_loops", 1)

# Highlight specific residues if provided
"""
        
        if highlight_residues:
            residues_str = "+".join(map(str, highlight_residues))
            script += f"""
# Highlight specific residues in red
cmd.select("highlight_res", "resi {residues_str}")
cmd.show("sticks", "highlight_res")
cmd.color("red", "highlight_res")
cmd.set("stick_radius", 0.3, "highlight_res")
"""
        
        script += f"""
# Show ligands
cmd.select("ligand_ref", "reference and resn UNK")
cmd.select("ligand_novel", "novel and resn UNK")
cmd.show("sticks", "ligand_ref")
cmd.show("sticks", "ligand_novel")
cmd.color("deepolive", "ligand_ref")
cmd.color("tv_red", "ligand_novel")
cmd.set("stick_radius", 0.35)
cmd.set("stick_transparency", 0)

# Show interacting residues (4Å cutoff)
cmd.select("interacting_res_ref", "byres (ligand_ref around 4)")
cmd.select("interacting_res_novel", "byres (ligand_novel around 4)")
cmd.show("sticks", "interacting_res_ref")
cmd.show("sticks", "interacting_res_novel")

# Color scheme for side chains
cmd.color("marine", "interacting_res_ref and name n+ca+c+o")
cmd.color("tv_red", "interacting_res_ref and not name n+ca+c+o")
cmd.color("marine", "interacting_res_novel and name n+ca+c+o")
cmd.color("tv_red", "interacting_res_novel and not name n+ca+c+o")

cmd.set("stick_radius", 0.2)
cmd.set("stick_transparency", 0)

# Add labels
cmd.label("interacting_res_ref and name ca", '"%s%s" % (resn, resi)')
cmd.label("interacting_res_novel and name ca", '"%s%s" % (resn, resi)')
cmd.set("label_color", "black")
cmd.set("label_size", 18)
cmd.set("label_font_id", 13)
cmd.set("label_outline_color", "grey70")
cmd.set("label_position", (0,0,3))

# Create pocket objects
cmd.create("pocket_ref", "interacting_res_ref")
cmd.create("pocket_novel", "interacting_res_novel")
cmd.show("mesh", "pocket_ref")
cmd.show("mesh", "pocket_novel")
cmd.color("palecyan", "pocket_ref")
cmd.color("lightblue", "pocket_novel")
cmd.set("mesh_width", 0.2)
cmd.set("transparency", 0.10, "pocket_ref")
cmd.set("transparency", 0.10, "pocket_novel")
cmd.set("mesh_mode", 1)

# Rendering settings
cmd.set("bg_rgb", "white")
cmd.set("ray_shadows", 0)
cmd.set("depth_cue", 0)
cmd.set("antialias", 2)
cmd.set("ray_trace_mode", 1)
cmd.set("ray_trace_gain", 0.1)
cmd.set("cartoon_side_chain_helper", "on")

# Orient and zoom
cmd.orient()
cmd.zoom("ligand_ref", buffer=12)

# Color by chain
cmd.util.cbc()

# Additional rendering settings
cmd.set("ray_texture", 1)
cmd.set("ray_shadow_decay_factor", 0.05)
cmd.set("ray_trace_frames", 3)

# Save high-resolution image
cmd.png("{self.output_dir}/{scene_name}.png", dpi=600)

print("Comparative scene created successfully!")
"""
        
        return script
    
    def _generate_interaction_script(self, pdb_file: Path, ligand_resname: str,
                                   cutoff_distance: float, scene_name: str) -> str:
        """Generate PyMOL script for interaction analysis."""
        
        script = f"""
# PyMOL Script for Interaction Analysis: {scene_name}
# Generated by PDB Prepare Wizard Post-Docking Analysis

# Clear workspace
cmd.delete("all")

# Load structure
cmd.load("{pdb_file}", "structure")

# Basic visualization setup
cmd.show("cartoon", "all")
cmd.color("gray78", "all")
cmd.set("cartoon_transparency", 0.55)
cmd.set("cartoon_smooth_loops", 1)

# Show ligand
cmd.select("ligand", "resn {ligand_resname}")
cmd.show("sticks", "ligand")
cmd.color("deepolive", "ligand")
cmd.set("stick_radius", 0.35)
cmd.set("stick_transparency", 0)

# Show interacting residues
cmd.select("interacting_res", "byres (ligand around {cutoff_distance})")
cmd.show("sticks", "interacting_res")

# Color scheme for side chains
cmd.color("marine", "interacting_res and name n+ca+c+o")
cmd.color("tv_red", "interacting_res and not name n+ca+c+o")

cmd.set("stick_radius", 0.2)
cmd.set("stick_transparency", 0)

# Add labels
cmd.label("interacting_res and name ca", '"%s%s" % (resn, resi)')
cmd.set("label_color", "black")
cmd.set("label_size", 18)
cmd.set("label_font_id", 13)
cmd.set("label_outline_color", "grey70")
cmd.set("label_position", (0,0,3))

# Create pocket object
cmd.create("pocket_obj", "interacting_res")
cmd.show("mesh", "pocket_obj")
cmd.color("palecyan", "pocket_obj")
cmd.set("mesh_width", 0.2)
cmd.set("transparency", 0.10, "pocket_obj")
cmd.set("mesh_mode", 1)

# Rendering settings
cmd.set("bg_rgb", "white")
cmd.set("ray_shadows", 0)
cmd.set("depth_cue", 0)
cmd.set("antialias", 2)
cmd.set("ray_trace_mode", 1)
cmd.set("ray_trace_gain", 0.1)
cmd.set("cartoon_side_chain_helper", "on")

# Orient and zoom
cmd.orient()
cmd.zoom("ligand", buffer=12)

# Color by chain
cmd.util.cbc()

# Additional rendering settings
cmd.set("ray_texture", 1)
cmd.set("ray_shadow_decay_factor", 0.05)
cmd.set("ray_trace_frames", 3)

# Save high-resolution image
cmd.png("{self.output_dir}/{scene_name}.png", dpi=600)

print("Interaction analysis created successfully!")
"""
        
        return script
    
    def _generate_gallery_script(self, pdb_files: List[Path], scene_name: str) -> str:
        """Generate PyMOL script for best poses gallery."""
        
        script = f"""
# PyMOL Script for Best Poses Gallery: {scene_name}
# Generated by PDB Prepare Wizard Post-Docking Analysis

# Clear workspace
cmd.delete("all")

# Load all structures
"""
        
        for i, pdb_file in enumerate(pdb_files):
            object_name = f"pose_{i+1}"
            script += f'cmd.load("{pdb_file}", "{object_name}")\n'
        
        script += """
# Basic visualization setup
cmd.show("cartoon", "all")
cmd.color("gray78", "all")
cmd.set("cartoon_transparency", 0.55)
cmd.set("cartoon_smooth_loops", 1)

# Show ligands
cmd.select("all_ligands", "resn UNK")
cmd.show("sticks", "all_ligands")
cmd.color("deepolive", "all_ligands")
cmd.set("stick_radius", 0.35)
cmd.set("stick_transparency", 0)

# Show interacting residues
cmd.select("all_interacting", "byres (all_ligands around 4)")
cmd.show("sticks", "all_interacting")
cmd.color("marine", "all_interacting and name n+ca+c+o")
cmd.color("tv_red", "all_interacting and not name n+ca+c+o")
cmd.set("stick_radius", 0.2)
cmd.set("stick_transparency", 0)

# Rendering settings
cmd.set("bg_rgb", "white")
cmd.set("ray_shadows", 0)
cmd.set("depth_cue", 0)
cmd.set("antialias", 2)
cmd.set("ray_trace_mode", 1)
cmd.set("ray_trace_gain", 0.1)
cmd.set("cartoon_side_chain_helper", "on")

# Orient and zoom
cmd.orient()
cmd.zoom("all_ligands", buffer=12)

# Color by chain
cmd.util.cbc()

# Additional rendering settings
cmd.set("ray_texture", 1)
cmd.set("ray_shadow_decay_factor", 0.05)
cmd.set("ray_trace_frames", 3)

# Save high-resolution image
cmd.png("{self.output_dir}/{scene_name}.png", dpi=600)

print("Best poses gallery created successfully!")
"""
        
        return script
    
    def _execute_pymol_script(self, script_file: Path):
        """Execute PyMOL script."""
        try:
            # Try to execute PyMOL script
            result = subprocess.run(
                ["pymol", "-c", "-q", str(script_file)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                print(f"⚠️ PyMOL execution warning: {result.stderr}")
            else:
                print("✅ PyMOL script executed successfully")
                
        except subprocess.TimeoutExpired:
            print("⚠️ PyMOL script execution timed out")
        except FileNotFoundError:
            print("⚠️ PyMOL not found. Please install PyMOL to use 3D visualization features.")
        except Exception as e:
            print(f"⚠️ Error executing PyMOL script: {e}")
    
    def _save_pymol_session(self, session_file: Path):
        """Save PyMOL session."""
        try:
            # Create a simple script to save session
            save_script = f"""
cmd.save("{session_file}")
print("Session saved successfully!")
"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pml', delete=False) as f:
                f.write(save_script)
                temp_script = f.name
            
            subprocess.run(
                ["pymol", "-c", "-q", temp_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            os.unlink(temp_script)
            
        except Exception as e:
            print(f"⚠️ Error saving PyMOL session: {e}")

def create_comparative_analysis(reference_pdb: Path, novel_pdb: Path,
                              output_dir: Path, highlight_residues: List[int] = None) -> Dict:
    """
    Create comprehensive comparative analysis between reference and novel compounds.
    
    Parameters
    ----------
    reference_pdb : Path
        Path to reference structure
    novel_pdb : Path
        Path to novel compound structure
    output_dir : Path
        Output directory
    highlight_residues : List[int], optional
        Residues to highlight
        
    Returns
    -------
    Dict
        Dictionary containing analysis results
    """
    print("🔬 Creating comparative analysis...")
    
    visualizer = PyMOLVisualizer(output_dir)
    
    # Create comparative scene
    comparative_session = visualizer.create_comparative_scene(
        reference_pdb, novel_pdb, highlight_residues, "comparative_analysis"
    )
    
    # Create individual interaction analyses
    ref_interaction = visualizer.create_interaction_analysis(
        reference_pdb, "UNK", 4.0, "reference_interactions"
    )
    
    novel_interaction = visualizer.create_interaction_analysis(
        novel_pdb, "UNK", 4.0, "novel_interactions"
    )
    
    analysis_results = {
        'comparative_session': comparative_session,
        'reference_interactions': ref_interaction,
        'novel_interactions': novel_interaction,
        'output_directory': output_dir
    }
    
    print("✅ Comparative analysis completed")
    return analysis_results


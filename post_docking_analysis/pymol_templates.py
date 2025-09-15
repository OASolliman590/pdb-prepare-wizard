PYMOL_SCENE_TEMPLATE = """
# Auto-generated PyMOL visualization for a complex
reinitialize

# Load structures
load {complex_pdb}, complex

# Basic scene
hide everything, all
show cartoon, all
color gray78, all
set cartoon_transparency, 0.55
set cartoon_smooth_loops, 1

# Ligand (UNK) highlight
select ligand, resn UNK
show sticks, ligand
color deepolive, ligand
set stick_radius, 0.35
set stick_transparency, 0

# Highlight specific residues in red
select highlight_res, resi 212+213+214
show sticks, highlight_res
color red, highlight_res
set stick_radius, 0.3, highlight_res

# Interacting residues within 4 Å
select interacting_res, byres (ligand around 4)
show sticks, interacting_res

# Color scheme for side chains
color marine, interacting_res and name n+ca+c+o
color tv_red, interacting_res and not name n+ca+c+o

set stick_radius, 0.2
set stick_transparency, 0

# Labels
label interacting_res and name ca, "%s%s" % (resn, resi)
set label_color, black
set label_size, 18
set label_font_id, 13
set label_outline_color, grey70
set label_position, (0,0,3)

# Pocket mesh around interacting residues
create pocket_obj, interacting_res
show mesh, pocket_obj
color palecyan, pocket_obj
set mesh_width, 0.2
set transparency, 0.10, pocket_obj
set mesh_mode, 1

# Clean scene
set bg_rgb, white
set ray_shadows, 0
set depth_cue, 0
set antialias, 2
set ray_trace_mode, 1
set ray_trace_gain, 0.1
set cartoon_side_chain_helper, on

# Camera
orient
zoom ligand, buffer=12
util.cbc

set ray_texture, 1
set ray_shadow_decay_factor, 0.05
set ray_trace_frames, 3

# Save outputs
save {session_out}
png {png_out}, dpi=600
"""

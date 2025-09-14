# PLIP Interaction Types Comprehensive Guide

## Overview
This document provides a comprehensive guide to all PLIP (Protein-Ligand Interaction Profiler) interaction types and their table structures in text reports. This ensures we don't miss any interaction types in future analyses.

## Complete List of PLIP Interaction Types

### 1. **Hydrophobic Interactions**
- **Description**: Non-polar interactions between hydrophobic regions
- **Table Columns**: 11
- **Distance Column**: 6 (DIST)
- **Header**: `RESNR | RESTYPE | RESCHAIN | RESNR_LIG | RESTYPE_LIG | RESCHAIN_LIG | DIST | LIGCARBONIDX | PROTCARBONIDX | LIGCOO | PROTCOO`
- **Status**: ✅ Fully implemented

### 2. **Hydrogen Bonds**
- **Description**: H-bonds between donor and acceptor groups
- **Table Columns**: 17
- **Distance Column**: 7 (DIST_H-A)
- **Header**: `RESNR | RESTYPE | RESCHAIN | RESNR_LIG | RESTYPE_LIG | RESCHAIN_LIG | SIDECHAIN | DIST_H-A | DIST_D-A | DON_ANGLE | PROTISDON | DONORIDX | DONORTYPE | ACCEPTORIDX | ACCEPTORTYPE | LIGCOO | PROTCOO`
- **Status**: ✅ Fully implemented

### 3. **Halogen Bonds**
- **Description**: Interactions involving halogen atoms (F, Cl, Br, I)
- **Table Columns**: 16
- **Distance Column**: 7 (DIST)
- **Header**: `RESNR | RESTYPE | RESCHAIN | RESNR_LIG | RESTYPE_LIG | RESCHAIN_LIG | SIDECHAIN | DIST | DON_ANGLE | ACC_ANGLE | DON_IDX | DONORTYPE | ACC_IDX | ACCEPTORTYPE | LIGCOO | PROTCOO`
- **Status**: ✅ Fully implemented

### 4. **Water Bridges**
- **Description**: H-bonds mediated by water molecules
- **Table Columns**: 19
- **Distance Column**: 6 (DIST_A-W)
- **Header**: `RESNR | RESTYPE | RESCHAIN | RESNR_LIG | RESTYPE_LIG | RESCHAIN_LIG | DIST_A-W | DIST_D-W | DON_ANGLE | WATER_ANGLE | PROTISDON | DONOR_IDX | DONORTYPE | ACCEPTOR_IDX | ACCEPTORTYPE | WATER_IDX | LIGCOO | PROTCOO | WATERCOO`
- **Status**: ✅ Fully implemented

### 5. **π-Stacking**
- **Description**: π-π stacking between aromatic rings
- **Table Columns**: 14
- **Distance Column**: 7 (CENTDIST)
- **Header**: `RESNR | RESTYPE | RESCHAIN | RESNR_LIG | RESTYPE_LIG | RESCHAIN_LIG | PROT_IDX_LIST | CENTDIST | ANGLE | OFFSET | TYPE | LIG_IDX_LIST | LIGCOO | PROTCOO`
- **Status**: ✅ Fully implemented

### 6. **Salt Bridges**
- **Description**: Ionic interactions between charged groups
- **Table Columns**: Unknown (need example)
- **Distance Column**: Estimated 6
- **Status**: ⚠️ Configuration ready, needs real example

### 7. **Metal Complexes**
- **Description**: Coordination bonds with metal ions
- **Table Columns**: Unknown (need example)
- **Distance Column**: Estimated 6
- **Status**: ⚠️ Configuration ready, needs real example

### 8. **π-Cation Interactions**
- **Description**: Interactions between cations and π-systems
- **Table Columns**: Unknown (need example)
- **Distance Column**: Estimated 6
- **Status**: ⚠️ Configuration ready, needs real example

## Implementation Details

### Parsing Configuration
```python
interaction_configs = {
    '**Hydrophobic Interactions**': {
        'key': 'hydrophobic',
        'min_columns': 8,
        'distance_col': 6
    },
    '**Hydrogen Bonds**': {
        'key': 'hydrogen_bonds', 
        'min_columns': 10,
        'distance_col': 7  # DIST_H-A
    },
    '**Halogen Bonds**': {
        'key': 'halogen_bonds',
        'min_columns': 8,
        'distance_col': 7  # DIST
    },
    '**Water Bridges**': {
        'key': 'water_bridges',
        'min_columns': 10,
        'distance_col': 6  # DIST_A-W
    },
    '**pi-Stacking**': {
        'key': 'pi_stacking',
        'min_columns': 10,
        'distance_col': 7  # CENTDIST
    },
    '**Salt Bridges**': {
        'key': 'salt_bridges',
        'min_columns': 8,
        'distance_col': 6  # Estimated
    },
    '**Metal Complexes**': {
        'key': 'metal_complexes',
        'min_columns': 8,
        'distance_col': 6  # Estimated
    },
    '**pi-Cation Interactions**': {
        'key': 'pi_cation',
        'min_columns': 8,
        'distance_col': 6  # Estimated
    }
}
```

### Key Features
1. **Unified Parsing**: Single parsing loop handles all interaction types
2. **Unknown Type Detection**: Automatically detects and reports unknown interaction types
3. **Robust Error Handling**: Gracefully handles parsing errors
4. **Future-Proof**: Easy to add new interaction types

## Test Results

### 3LN1_COX2 (CEL) - Perfect Match ✅
- **Hydrophobic**: 8 interactions
- **Hydrogen Bonds**: 5 interactions  
- **Halogen Bonds**: 1 interaction (ARG_106)
- **Total**: 13 residues, 132 atoms

### 2X22_INHA (NAD) - All Types Detected ✅
- **Hydrophobic**: 3 interactions
- **Hydrogen Bonds**: 13 interactions
- **π-Stacking**: 1 interaction (PHE_41)
- **Water Bridges**: 8 interactions
- **Total**: 18 residues, 192 atoms

## Future Enhancements

### Adding New Interaction Types
1. Find a PDB structure that contains the new interaction type
2. Run PLIP analysis and examine the text report
3. Identify the table structure (columns, distance column)
4. Add configuration to `interaction_configs`
5. Test with the new structure

### Monitoring for Unknown Types
The system automatically detects unknown interaction types and reports them:
```
⚠️ Found unknown interaction types: {'**New Interaction Type**'}
   Please update interaction_configs to handle these types
```

## References
- [PLIP GitHub Repository](https://github.com/pharmai/plip)
- [PLIP Documentation](https://plip.readthedocs.io/)
- [PLIP Web Server](https://plip-tool.biotec.tu-dresden.de/)

## Version History
- **v1.0**: Initial implementation with basic interaction types
- **v2.0**: Added halogen bonds support
- **v3.0**: Comprehensive implementation with all known interaction types
- **v3.1**: Added unknown type detection and future-proofing

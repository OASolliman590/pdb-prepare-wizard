#!/usr/bin/env python3
"""
Test script for PDB Prepare Wizard Pipeline
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_dependencies():
    """Test if all required dependencies are available."""
    print("🔍 Testing dependencies...")
    
    try:
        import numpy as np
        print("✓ NumPy available")
    except ImportError:
        print("❌ NumPy not available")
        return False
    
    try:
        import pandas as pd
        print("✓ Pandas available")
    except ImportError:
        print("❌ Pandas not available")
        return False
    
    try:
        from Bio.PDB import PDBParser
        print("✓ Biopython available")
    except ImportError:
        print("❌ Biopython not available")
        return False
    
    try:
        import plip
        print("✓ PLIP available")
    except ImportError:
        print("⚠️  PLIP not available (optional)")
    
    return True

def test_pipeline_initialization():
    """Test pipeline initialization."""
    print("\n🔍 Testing pipeline initialization...")
    
    try:
        from PDP_prep_improved import MolecularDockingPipeline
        pipeline = MolecularDockingPipeline(output_dir="test_output")
        print("✓ Pipeline initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        return False

def test_pdb_download():
    """Test PDB download functionality."""
    print("\n🔍 Testing PDB download...")
    
    try:
        from PDP_prep_improved import MolecularDockingPipeline
        pipeline = MolecularDockingPipeline(output_dir="test_output")
        
        # Test with a well-known PDB structure (HIV protease with inhibitor)
        pdb_file = pipeline.fetch_pdb("1HVR")
        
        if os.path.exists(pdb_file):
            print(f"✓ PDB download successful: {pdb_file}")
            return True
        else:
            print("❌ PDB file not found after download")
            return False
            
    except Exception as e:
        print(f"❌ PDB download failed: {e}")
        return False

def test_hetatm_enumeration():
    """Test HETATM enumeration."""
    print("\n🔍 Testing HETATM enumeration...")
    
    try:
        from PDP_prep_improved import MolecularDockingPipeline
        pipeline = MolecularDockingPipeline(output_dir="test_output")
        
        # Use the downloaded PDB file
        pdb_file = "test_output/1HVR.pdb"
        if not os.path.exists(pdb_file):
            print("❌ PDB file not found for testing")
            return False
        
        hetatm_details, unique_hetatms = pipeline.enumerate_hetatms(pdb_file)
        
        if hetatm_details:
            print(f"✓ Found {len(hetatm_details)} HETATM instances")
            print(f"✓ Unique HETATMs: {unique_hetatms}")
            return True
        else:
            print("❌ No HETATMs found")
            return False
            
    except Exception as e:
        print(f"❌ HETATM enumeration failed: {e}")
        return False

def test_structure_cleaning():
    """Test structure cleaning functionality."""
    print("\n🔍 Testing structure cleaning...")
    
    try:
        from PDP_prep_improved import MolecularDockingPipeline
        pipeline = MolecularDockingPipeline(output_dir="test_output")
        
        pdb_file = "test_output/1HVR.pdb"
        if not os.path.exists(pdb_file):
            print("❌ PDB file not found for testing")
            return False
        
        # Test cleaning with common residues
        cleaned_pdb = pipeline.clean_pdb(
            pdb_file, 
            to_remove_list=['HOH', 'NA', 'CL'],
            output_filename="test_output/cleaned_test.pdb"
        )
        
        if os.path.exists(cleaned_pdb):
            print(f"✓ Structure cleaning successful: {cleaned_pdb}")
            return True
        else:
            print("❌ Cleaned PDB file not found")
            return False
            
    except Exception as e:
        print(f"❌ Structure cleaning failed: {e}")
        return False

def test_pocket_analysis():
    """Test pocket analysis functionality."""
    print("\n🔍 Testing pocket analysis...")
    
    try:
        from PDP_prep_improved import MolecularDockingPipeline
        pipeline = MolecularDockingPipeline(output_dir="test_output")
        
        cleaned_pdb = "test_output/cleaned_test.pdb"
        if not os.path.exists(cleaned_pdb):
            print("❌ Cleaned PDB file not found for testing")
            return False
        
        # Test with arbitrary coordinates (center of structure)
        import numpy as np
        center_coords = np.array([0.0, 0.0, 0.0])
        
        pocket_results = pipeline.analyze_pocket_properties(cleaned_pdb, center_coords)
        
        if pocket_results:
            print("✓ Pocket analysis completed")
            print(f"  - Electrostatic score: {pocket_results.get('electrostatic_score', 'N/A')}")
            print(f"  - Hydrophobic score: {pocket_results.get('hydrophobic_score', 'N/A')}")
            print(f"  - Druggability score: {pocket_results.get('druggability_score', 'N/A')}")
            return True
        else:
            print("❌ Pocket analysis failed")
            return False
            
    except Exception as e:
        print(f"❌ Pocket analysis failed: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary."""
    print("🧪 Running PDB Prepare Wizard Tests")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Pipeline Initialization", test_pipeline_initialization),
        ("PDB Download", test_pdb_download),
        ("HETATM Enumeration", test_hetatm_enumeration),
        ("Structure Cleaning", test_structure_cleaning),
        ("Pocket Analysis", test_pocket_analysis),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The pipeline is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
        return False

def cleanup_test_files():
    """Clean up test files."""
    print("\n🧹 Cleaning up test files...")
    
    test_dir = Path("test_output")
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
        print("✓ Test files cleaned up")

if __name__ == "__main__":
    try:
        success = run_all_tests()
        
        if success:
            print("\n✅ Pipeline is working correctly!")
        else:
            print("\n❌ Some issues were found. Please check the requirements and dependencies.")
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
    finally:
        # Ask user if they want to clean up
        try:
            cleanup_choice = input("\nClean up test files? (y/n): ").lower().strip()
            if cleanup_choice == 'y':
                cleanup_test_files()
        except:
            pass 
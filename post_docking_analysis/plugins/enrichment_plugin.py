"""
Enrichment Analysis Plugin
"""

from pathlib import Path

PLUGIN_NAME = "Enrichment Analyzer"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Analysis plugin for compound enrichment assessment"
PLUGIN_AUTHOR = "PDB Prepare Wizard Team"

def analyze(data: dict, output_dir: Path, config: dict) -> dict:
    """
    Analyze compound enrichment from docking data.
    
    Parameters
    ----------
    data : dict
        Input data from the pipeline
    output_dir : Path
        Output directory for results
    config : dict
        Plugin configuration
        
    Returns
    -------
    dict
        Analysis results
    """
    import pandas as pd
    import numpy as np
    from pathlib import Path
    
    # Create output directory for this plugin
    plugin_output_dir = output_dir / "enrichment_analysis"
    plugin_output_dir.mkdir(exist_ok=True)
    
    # Extract relevant data
    if 'best_poses' not in data:
        return {
            "plugin": PLUGIN_NAME,
            "status": "failed",
            "error": "No best poses data available for analysis"
        }
    
    df = data['best_poses']
    
    # Perform enrichment analysis
    if 'vina_affinity' in df.columns and 'complex_name' in df.columns:
        # Extract protein from complex_name if protein column doesn't exist
        if 'protein' not in df.columns:
            def extract_protein(complex_name):
                if '_' in complex_name:
                    parts = complex_name.split('_')
                    if len(parts) >= 2:
                        return f"{parts[0]}_{parts[1]}"  # e.g., 4TRO_INHA
                    else:
                        return parts[0]
                return complex_name
            
            df = df.copy()
            df['protein'] = df['complex_name'].apply(extract_protein)
        
        # Calculate enrichment metrics
        strong_binder_threshold = config.get('strong_binder_threshold', -8.0)
        
        # Identify strong binders
        strong_binders = df[df['vina_affinity'] <= strong_binder_threshold]
        
        # Calculate enrichment by protein
        protein_enrichment = df.groupby('protein').agg({
            'vina_affinity': ['count', lambda x: (x <= strong_binder_threshold).sum()]
        }).round(3)
        
        # Flatten column names
        protein_enrichment.columns = ['total_compounds', 'strong_binders']
        protein_enrichment = protein_enrichment.reset_index()
        
        # Calculate enrichment ratio
        protein_enrichment['enrichment_ratio'] = (
            protein_enrichment['strong_binders'] / protein_enrichment['total_compounds']
        ).round(3)
        
        # Sort by enrichment ratio
        protein_enrichment = protein_enrichment.sort_values('enrichment_ratio', ascending=False)
        
        # Save enrichment data
        enrichment_file = plugin_output_dir / "protein_enrichment.csv"
        protein_enrichment.to_csv(enrichment_file, index=False)
        
        # Identify top enriched proteins
        top_enriched = protein_enrichment.head(5)
        
        # Create enrichment summary report
        summary_file = plugin_output_dir / "enrichment_summary.txt"
        with open(summary_file, 'w') as f:
            f.write("Compound Enrichment Analysis Summary\n")
            f.write("===================================\n\n")
            f.write(f"Total compounds analyzed: {len(df)}\n")
            f.write(f"Strong binders (≤{strong_binder_threshold} kcal/mol): {len(strong_binders)}\n")
            f.write(f"Overall enrichment rate: {len(strong_binders)/len(df)*100:.1f}%\n\n")
            f.write("Top Enriched Proteins:\n")
            for _, row in top_enriched.iterrows():
                f.write(f"  {row['protein']}: {row['enrichment_ratio']*100:.1f}% ({row['strong_binders']}/{row['total_compounds']})\n")
        
        results = {
            "plugin": PLUGIN_NAME,
            "status": "completed",
            "total_compounds": len(df),
            "strong_binders": len(strong_binders),
            "enrichment_threshold": strong_binder_threshold,
            "enrichment_data_file": str(enrichment_file),
            "summary_file": str(summary_file),
            "top_enriched_proteins": top_enriched.to_dict('records')
        }
    else:
        results = {
            "plugin": PLUGIN_NAME,
            "status": "completed",
            "message": "Required columns (vina_affinity, complex_name) not found in data"
        }
    
    return results
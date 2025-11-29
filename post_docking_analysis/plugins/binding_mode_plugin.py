"""
Binding Mode Analysis Plugin
"""

from pathlib import Path

PLUGIN_NAME = "Binding Mode Analyzer"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Analysis plugin for binding mode clustering"
PLUGIN_AUTHOR = "PDB Prepare Wizard Team"

def analyze(data: dict, output_dir: Path, config: dict) -> dict:
    """
    Analyze binding modes from docking data.
    
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
    from sklearn.cluster import KMeans
    
    # Create output directory for this plugin
    plugin_output_dir = output_dir / "binding_mode_analysis"
    plugin_output_dir.mkdir(exist_ok=True)
    
    # Extract relevant data
    if 'full_data' not in data:
        return {
            "plugin": PLUGIN_NAME,
            "status": "failed",
            "error": "No full data available for analysis"
        }
    
    df = data['full_data']
    
    # Perform binding mode analysis based on available data
    if 'vina_affinity' in df.columns:
        # Since we don't have RMSD data, perform affinity-based clustering
        features = df[['vina_affinity']].dropna()
        
        if len(features) > 3:  # Need at least 3 points for meaningful clustering
            # Perform K-means clustering based on affinity
            kmeans = KMeans(n_clusters=min(3, len(features)), random_state=42)
            cluster_labels = kmeans.fit_predict(features)
            
            # Add cluster labels to dataframe
            df_clustered = df.copy()
            df_clustered['binding_mode'] = cluster_labels
            
            # Categorize binding modes based on affinity ranges
            def categorize_binding_mode(affinity):
                if affinity <= -10.0:
                    return "High Affinity"
                elif affinity <= -7.0:
                    return "Medium Affinity"
                else:
                    return "Low Affinity"
            
            df_clustered['affinity_category'] = df_clustered['vina_affinity'].apply(categorize_binding_mode)
            
            # Save clustered data
            clustered_file = plugin_output_dir / "binding_modes.csv"
            df_clustered.to_csv(clustered_file, index=False)
            
            # Calculate cluster statistics
            cluster_stats = df_clustered.groupby('binding_mode').agg({
                'vina_affinity': ['mean', 'std', 'count', 'min', 'max']
            }).round(3)
            
            # Flatten column names
            cluster_stats.columns = ['_'.join(col).strip() for col in cluster_stats.columns]
            cluster_stats = cluster_stats.reset_index()
            
            # Save cluster statistics
            stats_file = plugin_output_dir / "binding_mode_statistics.csv"
            cluster_stats.to_csv(stats_file, index=False)
            
            # Create binding mode summary
            summary_file = plugin_output_dir / "binding_mode_summary.txt"
            with open(summary_file, 'w') as f:
                f.write("Binding Mode Analysis Summary\n")
                f.write("============================\n\n")
                f.write(f"Total poses analyzed: {len(df_clustered)}\n")
                f.write(f"Number of binding modes: {len(cluster_stats)}\n\n")
                f.write("Binding Mode Statistics:\n")
                for _, row in cluster_stats.iterrows():
                    f.write(f"  Mode {row['binding_mode']}: {row['vina_affinity_count']} poses, ")
                    f.write(f"affinity range {row['vina_affinity_min']:.2f} to {row['vina_affinity_max']:.2f} kcal/mol\n")
            
            results = {
                "plugin": PLUGIN_NAME,
                "status": "completed",
                "num_clusters": len(cluster_stats),
                "total_poses": len(df_clustered),
                "clustered_data_file": str(clustered_file),
                "statistics_file": str(stats_file),
                "summary_file": str(summary_file),
                "cluster_statistics": cluster_stats.to_dict('records')
            }
        else:
            results = {
                "plugin": PLUGIN_NAME,
                "status": "completed",
                "message": "Insufficient data for binding mode clustering"
            }
    else:
        results = {
            "plugin": PLUGIN_NAME,
            "status": "completed",
            "message": "Required column (vina_affinity) not found in data"
        }
    
    return results
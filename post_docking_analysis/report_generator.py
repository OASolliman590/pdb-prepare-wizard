"""
Report generator for post-docking analysis pipeline.

This module handles the generation of summary reports in various formats.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List
import json
import csv

def generate_csv_reports(analysis_results: Dict[str, pd.DataFrame], output_dir: Path):
    """
    Generate CSV reports from analysis results.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for reports
    """
    print("📝 Generating CSV reports...")
    
    # Create output directory
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Generate individual CSV files for each result type
    for name, df in analysis_results.items():
        if isinstance(df, pd.DataFrame):
            csv_file = reports_dir / f"{name}.csv"
            df.to_csv(csv_file, index=False)
            print(f"✅ {name} report saved to: {csv_file}")
    
    print("✅ CSV reports generated successfully!")

def generate_excel_report(analysis_results: Dict[str, pd.DataFrame], output_dir: Path):
    """
    Generate an Excel report from analysis results.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for reports
    """
    print("📝 Generating Excel report...")
    
    # Check if openpyxl is available
    try:
        import openpyxl
    except ImportError:
        print("⚠️  openpyxl not available - Excel report generation skipped")
        return
    
    # Create output directory
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Generate Excel file with multiple sheets
    excel_file = reports_dir / "docking_analysis_results.xlsx"
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        for name, df in analysis_results.items():
            if isinstance(df, pd.DataFrame):
                # Limit sheet name to 31 characters (Excel limit)
                sheet_name = name[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"✅ Excel report saved to: {excel_file}")

def generate_summary_report(analysis_results: Dict[str, pd.DataFrame], output_dir: Path):
    """
    Generate a summary report with key findings.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for reports
    """
    print("📝 Generating summary report...")
    
    # Create output directory
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Get key results
    best_poses = analysis_results['best_poses']
    summary_stats = analysis_results['summary_stats']
    
    # Generate summary text
    summary_lines = [
        "Post-Docking Analysis Summary Report",
        "==================================",
        "",
        f"Total complexes analyzed: {len(best_poses)}",
        f"Average binding affinity: {best_poses['vina_affinity'].mean():.2f} kcal/mol",
        f"Best binding affinity: {best_poses['vina_affinity'].min():.2f} kcal/mol",
        f"Worst binding affinity: {best_poses['vina_affinity'].max():.2f} kcal/mol",
        "",
        "Top 5 Performers:",
    ]
    
    # Add top 5 performers
    top_5 = best_poses.head(5)
    for idx, (_, row) in enumerate(top_5.iterrows(), 1):
        summary_lines.append(
            f"  {idx}. {row['complex_name']}: {row['vina_affinity']:.2f} kcal/mol"
        )
    
    # Save summary report
    summary_file = reports_dir / "summary_report.txt"
    with open(summary_file, 'w') as f:
        f.write('\n'.join(summary_lines))
    
    print(f"✅ Summary report saved to: {summary_file}")

def generate_json_report(analysis_results: Dict[str, pd.DataFrame], output_dir: Path):
    """
    Generate a JSON report from analysis results.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for reports
    """
    print("📝 Generating JSON report...")
    
    # Create output directory
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Convert DataFrames to dictionaries for JSON serialization
    json_data = {}
    for name, df in analysis_results.items():
        if isinstance(df, pd.DataFrame):
            json_data[name] = df.to_dict(orient='records')
    
    # Save JSON report
    json_file = reports_dir / "analysis_results.json"
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"✅ JSON report saved to: {json_file}")

def generate_all_reports(analysis_results: Dict[str, pd.DataFrame], output_dir: Path):
    """
    Generate all reports.
    
    Parameters
    ----------
    analysis_results : Dict[str, pd.DataFrame]
        Dictionary containing analysis results
    output_dir : Path
        Output directory for reports
    """
    print("📝 Generating all reports...")
    
    generate_csv_reports(analysis_results, output_dir)
    generate_excel_report(analysis_results, output_dir)
    generate_summary_report(analysis_results, output_dir)
    generate_json_report(analysis_results, output_dir)
    
    print("✅ All reports generated successfully!")
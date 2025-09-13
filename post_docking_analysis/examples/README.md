# Post-Docking Analysis Pipeline - Examples

This directory contains example scripts and configuration files for running the post-docking analysis pipeline.

## Files

- `run_pipeline.py`: Example Python script demonstrating different ways to run the pipeline
- `example_config.json`: Sample configuration file

## Usage

### Running the Example Script

```bash
# Navigate to the examples directory
cd /path/to/pdb-prepare-wizard/post_docking_analysis/examples

# Run the example script
python run_pipeline.py
```

### Using the Example Configuration

```bash
# Navigate to the examples directory
cd /path/to/pdb-prepare-wizard/post_docking_analysis/examples

# Run the pipeline with the example configuration
python -m post_docking_analysis --config example_config.json
```

## Customization

You can modify the example configuration file to suit your needs:

1. Change `input_dir` to point to your docking results
2. Modify `output_dir` to specify where results should be saved
3. Enable or disable specific processing steps
4. Adjust file patterns for different directory structures

The example script demonstrates three different ways to run the pipeline:

1. **Basic Run**: Uses default settings with minimal configuration
2. **Configuration-Based Run**: Uses a JSON configuration file
3. **Minimal Run**: Disables most processing steps for faster execution
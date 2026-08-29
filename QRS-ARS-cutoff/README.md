# QRS-ARS Cutoff Dataset

## Overview

The QRS-ARS Cutoff dataset is used to calculate optimal Question Relevance Score (QRS) and Answer Relevance Score (ARS) cutoff thresholds for various embedding models in the MyGPT system. MyGPT provides precalculated cutoff values for 5 embedding models as follows:

| Model Name | Model Size (GB) | Source | Best Distance (Q) | Worst Distance (Q) | Best Distance (AC) | Worst Distance (AC) |
|---|---|---|---|---|---|---|
| nomic-embed-text:latest | 0.27 | ollama | 41.65 | 501.324 | 20.132 | 469.74 |
| nomic-embed-text-v2-moe:latest | 0.96 | ollama | 13.43 | 214.38 | 23.69 | 206.29 |
| bge-m3:latest | 1.16 | ollama | 81.44 | 820.82 | 164.86 | 736.67 |
| multi-qa-MiniLM-L6-cos-v1 | - | sentence-transformer | 0.074 | 0.96 | 0.074 | 0.61 |
| qwen3-embedding:latest | 4.68 | ollama | 0.086 | 1.647 | 0.133 | 1.165 |

Users interested in adding new embedding models should first download the necessary PDFs and create a MyGPT library with the appropriate embedding model.

For users interested in recalculating cutoff thresholds for their own use-case, should first create a library with their own documents and embedding model, and then run the pipeline to generate the necessary context and answer data for cutoff calculation.

## Folder Structure

```
QRS-ARS-cutoff/
├── inputs/
│   └── QRS_ARS_cutoff_dataset.csv   # Input dataset
├── outputs/
│   ├── contexts/                    # Generated context data
│   │   └── context_QRS-ARS-cutoff-nomic-moe.json
│   └── answers/                     # Generated answers and scores
│       ├── answers-gpt-oss-20b-QRS-ARS-cutoff-nomic-moe.json
│       ├── answers-gpt-oss-20b-QRS-ARS-cutoff-nomic-moe.csv
│       ├── answers-gpt-oss-20b-QRS-ARS-cutoff-nomic-moe-full.csv
│       ├── answers-gpt-oss-20b-QRS-ARS-cutoff-nomic-moe-full_row_min_max.csv
│       ├── answers-scores-gpt-oss-20b-QRS-ARS-cutoff-nomic-moe.csv
│       └── QRS_ARS_cutoff_nomic.csv
└── scripts/
    ├── collect_context.py           # Build context JSON
    ├── collect_answers.py           # Call LLM and store answers
    ├── save_answers.py              # Send answers to scoring API
    ├── format_answers.py            # Convert answer JSON to CSV
    ├── combine_answers.py           # Combine all results
    ├── copy_pubmedqa_pdfs.py        # Copy PDFs from PubMedQA dataset
    ├── extract_rowwise_min_max.py   # Add row-wise min/max features
    └── master_script.py             # Orchestrator for all steps
```

## Setup

First, collect PDFs for this dataset and create a MyGPT library with an embedding model to calculate QCbest, QCworst, ACbest, and ACworst values.

```bash
# Optional: Copy PDFs from PubMedQA dataset
python3 copy_pubmedqa_pdfs.py
```

## Running the Pipeline

### Option 1: Using the Orchestrator (Recommended)

From the `scripts/` directory:

```bash
python3 master_script.py --dataset QRS-ARS-cutoff-bge
```

You can replace the dataset parameter with other embedding models:

```bash
python3 master_script.py --dataset QRS-ARS-cutoff-nomic-moe
```

### Option 2: Running Scripts Manually

From the `scripts/` directory, run in order:

```bash
python3 collect_context.py
python3 collect_answers.py
python3 save_answers.py
python3 format_answers.py
python3 combine_answers.py
python3 extract_rowwise_min_max.py
```

## Resume / Checkpoint Behavior

The `master_script.py` orchestrator supports resume behavior:

- Skips scripts whose expected output files already exist
- For CSV checkpoints, requires at least 55 data rows (header not counted)
- If all final outputs are present and valid, exits without rerunning steps

## Input Format

- **File**: `inputs/QRS_ARS_cutoff_dataset.csv`
- Dataset for calculating cutoff thresholds

## Output Files

- **Context**: `outputs/contexts/context_QRS-ARS-cutoff-*.json` - Context data for each embedding model
- **Answers**: `outputs/answers/answers-gpt-oss-20b-QRS-ARS-cutoff-*.json` - LLM responses
- **Formatted Answers**: `outputs/answers/answers-gpt-oss-20b-QRS-ARS-cutoff-*.csv` - Answers in CSV format
- **With Features**: `outputs/answers/answers-gpt-oss-20b-QRS-ARS-cutoff-*-full_row_min_max.csv` - Answers with row-wise min/max features
- **Scores**: `outputs/answers/answers-scores-gpt-oss-20b-QRS-ARS-cutoff-*.csv` - Evaluation scores
- **Cutoff Results**: `outputs/answers/QRS_ARS_cutoff_*.csv` - Calculated cutoff thresholds

## Notes

- `save_answers.py` requires the local MyGPT API server running at `http://localhost:8000`
- If the API service is unavailable, the pipeline will fail at scoring and can be resumed once the service is restored
- Ensure `.env` file is configured with appropriate credentials before running scripts
- See the main [README.md](../README.md) for environment setup instructions

# BioASQ Dataset

## Overview

BioASQ is a biomedical question answering dataset used to evaluate the MyGPT system's performance on domain-specific QA tasks.

Subset of BioASQ: 

For the manuscript, we used a subset of the BioASQ dataset containing 3964 questions. The full dataset contains 163 questions.

The raw dataset is available at https://participants-area.bioasq.org/datasets/ as "13b golden enriched"

Based on the Power Analysis, we determined that a sample size of 163 would be sufficient for our study.


## Folder Structure

```
BioASQ/
├── inputs/
│   ├── questions_final.csv          # Input questions
|   └── pdfs/                        # PDFs to create the dataset
├── outputs/
│   ├── contexts/                    # Generated context data
│   │   └── context_Bioasq.json
│   └── answers/                     # Generated answers and scores
│       ├── answers-gpt-oss-20b-Bioasq.json
│       └── answers-scores-Bioasq-gpt-oss-20b.csv
└── scripts/
    ├── collect_context.py           # Build context JSON
    ├── collect_answers.py           # Call LLM and store answers
    ├── save_answers.py              # Send answers to scoring API
    ├── format_answers.py            # Convert answer JSON to CSV
    └── combine_answers.py           # Combine all results
```

## Running the Pipeline

Step 1: Create a MyGPT library named 'BioASQ' in MyGPT using PDFs from inputs/pdfs

    Use default settings of MyGPT to upload. 
    The uploading can take form 5-20 minutes based on configureation of your device.

    Note: if you use any other library name, make sure to update the references in the scripts accordingly in all the scripts in the `scripts/` directory.

Step 2: Run scripts to collect answers and scores.

    From the `scripts/` directory:

    ```bash
    python3 collect_context.py
    python3 collect_answers.py
    python3 save_answers.py
    python3 format_answers.py
    python3 combine_answers.py
    ```

## Input Format

- **File**: `inputs/questions_final.csv`
- Contains the biomedical questions to be evaluated

## Output Files

- **Context**: `outputs/contexts/context_Bioasq.json` - Context data used for answering
- **Answers**: `outputs/answers/answers-gpt-oss-20b-Bioasq.json` - LLM responses
- **Scores**: `outputs/answers/answers-scores-Bioasq-gpt-oss-20b.csv` - Evaluation scores

## Notes

- Ensure `.env` file is configured with appropriate credentials before running scripts
- See the main [README.md](../README.md) for environment setup instructions

# MyGPT Evaluations
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22165150.svg)](https://doi.org/10.5281/zenodo.22165150)

Comprehensive evaluation datasets and pipelines for the **MyGPT** retrieval-augmented generation system. This repository contains multiple benchmark datasets, evaluation scripts, and analysis tools used to assess MyGPT's performance across different domains and scenarios.

This repository is part of the **MyGPT research paper**. To run these evaluations, you must have MyGPT installed and running.

## Prerequisites

**MyGPT Installation Required**: These evaluation pipelines require a running instance of MyGPT. Users can deploy MyGPT in one of the following ways:

1. **Local Installation** – Install MyGPT on your machine (recommended for development)
2. **VM Deployment** – Run MyGPT on a virtual machine
3. **Cloud Hosting** – Deploy MyGPT on cloud infrastructure (AWS, Azure, GCP, etc.)

For detailed installation instructions, see the [MyGPT GitHub repository](https://github.com/stjude/MyGPT).

## Quick Start

### 1. Environment Setup

```bash
# Copy the environment template
cp env_example .env

# Edit .env with your credentials and service URLs
```

**Required environment variables:**

- `BACKEND_API_URL` – MyGPT backend API endpoint
- `OLLAMA_API_URL` – Ollama LLM API endpoint
- `API_USERNAME` – Authentication username
- `API_PASSWORD` – Authentication password

Note: If you don't have API_USERNAME and API_PASSWORD, you have to create a superuser account in MyGPT and use the credentials to run the evaluation pipeline. To create a superuser account, run the provided script with the installation guide for your operating system.

For example, on MacOS, you can run:

```bash
cd MyGPT/installation/macOS/prebuilt_images/
bash create_superuser.sh
```

### 2. Choose a Dataset and Follow Its README

Each evaluation dataset has its own folder with a dedicated README containing:
- Dataset overview and use cases
- Folder structure and expected files
- Input/output format documentation
- Step-by-step running instructions

## Datasets

This repository includes six major evaluation benchmarks:

| Dataset | Domain | Purpose | PDF Availability | Docs |
|---------|--------|---------|------------------|------|
| **BioASQ** | Biomedical | Domain-specific QA on biomedical literature | ✓ Provided | [→ BioASQ/README.md](BioASQ/README.md) |
| **PubMedQA** | Scientific | Question answering on PubMed abstracts with entity re-ranking | DOIs provided | [→ PubMedQA/README.md](PubMedQA/README.md) |
| **Open-rag-bench** | General | Open-domain QA with retrieval-augmented generation | Download script | [→ Open-rag-bench/README.md](Open-rag-bench/README.md) |
| **Health Policies** | Public health | Policy document QA across global health policy PDFs | ✓ Provided | [→ health_policies/README.md](health_policies/README.md) |
| **Kinase Literature** | Biomedical literature mining | Kinase-specific extraction from PubMed-linked papers | DOIs provided | [→ kinase_literature/README.md](kinase_literature/README.md) |
| **QRS-ARS Cutoff** | Multi-modal | Cutoff threshold calculation for embedding models | PubMed IDs provided | [→ QRS-ARS-cutoff/README.md](QRS-ARS-cutoff/README.md) |

## Standard Evaluation Pipeline

All datasets follow a consistent evaluation workflow:

1. **Collect Context** – Build retrieval contexts using the RAG system
2. **Collect Answers** – Generate answers using the LLM
3. **Score Answers** – Compute evaluation metrics via the scoring API
4. **Format Results** – Convert outputs to standardized CSV format
5. **Combine Data** – Merge answers, scores, and contexts into final datasets

Each dataset folder contains scripts for these steps in its `scripts/` directory.

## Repository Structure

```
.
├── README.md                          # This file
├── env_example                        # Environment configuration template
├── BioASQ/                            # Biomedical QA benchmark
│   ├── README.md                      # Dataset-specific documentation
│   ├── inputs/                        # Input questions/queries
│   ├── outputs/                       # Generated contexts and answers
│   └── scripts/                       # Evaluation pipeline scripts
├── PubMedQA/                          # PubMed scientific QA benchmark
│   ├── README.md
│   ├── inputs/
│   ├── outputs/
│   └── scripts/
├── Open-rag-bench/                    # General-domain RAG benchmark
│   ├── README.md
│   ├── inputs/
│   ├── outputs/
│   └── scripts/
├── health_policies/                   # Global health policy document QA
│   ├── README.md
│   ├── inputs/
│   └── scripts/
├── kinase_literature/                 # Kinase literature extraction benchmark
│   ├── README.md
│   ├── inputs/
│   ├── outputs/
│   └── scripts/
└── QRS-ARS-cutoff/                    # Embedding model cutoff calculation
    ├── README.md
    ├── inputs/
    ├── outputs/
    └── scripts/
```

## Getting Started with a Dataset

1. **Setup**: Complete the environment setup above (copy and configure `.env`)
2. **Navigate**: Enter the dataset folder (`cd BioASQ`, `cd PubMedQA`, etc.)
3. **Read**: Review the dataset's `README.md` for specific instructions
4. **Execute**: Follow the dataset's evaluation pipeline steps

Example for BioASQ:

```bash
cd BioASQ/scripts
python3 collect_context.py
python3 collect_answers.py
python3 save_answers.py
python3 format_answers.py
python3 combine_answers.py
```

Some datasets have preparation steps before the standard pipeline. For example, Open-rag-bench downloads arXiv PDFs, Health Policies requires creating the appropriate MyGPT policy library, and Kinase Literature can enrich PubMed IDs with DOI values before running retrieval.

## Advanced Features

- **Orchestrated Execution**: Some datasets provide orchestrator scripts that manage the full pipeline automatically with checkpoint/resume support
- **Flexible Thresholds**: QRS-ARS cutoff dataset supports multiple embedding models for threshold customization
- **Incremental Processing**: Pipelines check for existing outputs and can be resumed if interrupted

## Support and Documentation

For dataset-specific questions, implementation details, and troubleshooting:
- **BioASQ**: See [BioASQ/README.md](BioASQ/README.md)
- **PubMedQA**: See [PubMedQA/README.md](PubMedQA/README.md)
- **Open-rag-bench**: See [Open-rag-bench/README.md](Open-rag-bench/README.md)
- **Health Policies**: See [health_policies/README.md](health_policies/README.md)
- **Kinase Literature**: See [kinase_literature/README.md](kinase_literature/README.md)
- **QRS-ARS Cutoff**: See [QRS-ARS-cutoff/README.md](QRS-ARS-cutoff/README.md)

## License

This evaluation framework and datasets are provided as part of the MyGPT research project.

def generate_mock_pipeline(prompt: str) -> dict:
    return {
        "pipeline_type": "rna-seq-de",
        "description": f"Mock pipeline for: {prompt}",
        "tools": [
            {
                "name": "DESeq2",
                "version": "1.40.2",
                "container": {
                    "registry": "docker.io",
                    "image": "bioconductor/bioconductor_docker",
                    "tag": "RELEASE_3_18",
                    "full_uri": "docker.io/bioconductor/bioconductor_docker:RELEASE_3_18",
                    "source": "mock",
                },
                "purpose": "Differential expression analysis",
                "language": "R",
            }
        ],
        "rules": [
            {
                "name": "run_deseq2",
                "tool": "DESeq2",
                "input": ["counts/all_samples_counts.tsv"],
                "output": ["results/deseq2_results.tsv"],
                "params": {"design": "~ condition"},
                "shell_cmd": "Rscript scripts/run_deseq2.R counts/all_samples_counts.tsv results/deseq2_results.tsv",
                "resources": {"cpus": 2, "mem_mb": 4000, "time_min": 30, "disk_mb": 5000},
                "log": ["logs/deseq2.log"],
            }
        ],
        "dag_edges": [],
        "config_params": {"design": "~ condition", "contrast": ["condition", "B", "A"]},
        "wildcards": [],
    }
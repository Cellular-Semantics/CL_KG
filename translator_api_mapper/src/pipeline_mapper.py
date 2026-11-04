import logging
import sys

from gene_node_unifier.gene_node_unifier import gene_node_unifier
from pr_uniprot_id_swapper.pr_uniprot_id_swapper import pr_uniprot_id_swapper
from uniprot_gene_mapper.uniprot_gene_mapper import uniprot_gene_mapper
from utils.reporting import StepReport

logger = logging.getLogger("pipeline_mapper")

# Top-level packages of this pipeline; their module loggers inherit INFO.
PIPELINE_LOGGERS = (
    "pipeline_mapper",
    "gene_node_unifier",
    "pr_uniprot_id_swapper",
    "uniprot_gene_mapper",
    "utils",
)


def configure_logging() -> None:
    """Configure logging once: third-party libraries at WARNING, pipeline at INFO."""
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    for name in PIPELINE_LOGGERS:
        logging.getLogger(name).setLevel(logging.INFO)

# Steps run in order and never abort the pipeline: each is safe to re-run, so a
# failed batch is reported here and picked up by the next run.
STEPS = (
    # Swap CL PR term URIs with UniProtKB dbxref values CL_KG#53
    ("pr_uniprot_id_swapper", pr_uniprot_id_swapper),
    # Link from Proteins (uniprot) to Genes (Ensembl) CL_KG#73
    ("uniprot_gene_mapper", uniprot_gene_mapper),
    # Unify Genes (Ensembl) with NCBIGene nodes
    ("gene_node_unifier", gene_node_unifier),
)

def main() -> None:
    configure_logging()
    reports = []
    for name, step in STEPS:
        try:
            reports.append(step())
        except Exception as e:
            logger.exception(f"[{name}] crashed")
            reports.append(StepReport(name, failures=[f"crashed: {e}"]))

    logger.info("=== Translator API mapper summary ===")
    for report in reports:
        report.log_summary(logger)
    if all(report.ok for report in reports):
        logger.info("All steps completed without failures.")
    else:
        logger.error("Some steps reported failures; re-running the pipeline is safe.")


if __name__ == "__main__":
    main()

import logging

from pandasaurus_cxg.enrichment_analysis import AnndataEnrichmentAnalyzer
from pandasaurus_cxg.graph_generator.graph_generator import GraphGenerator

from bitmap_builder import build_cluster_bitmaps

logger = logging.getLogger(__name__)


def generate_rdf_graph(
    anndata_file_path: str,
    author_cell_type_list: list[str],
    output_rdf_path: str,
    dataset_metadata: dict | None = None,
    bitmap_output_dir: str | None = None,
):
    logger.info(f"Generating RDF graph using {anndata_file_path}...")
    aea = AnndataEnrichmentAnalyzer(anndata_file_path, author_cell_type_list)
    aea.analyzer_manager.co_annotation_report()
    gg = GraphGenerator(aea, dataset_metadata=dataset_metadata)
    gg.generate_rdf_graph(merge=True)
    gg.set_label_adding_priority(author_cell_type_list)
    gg.add_label_to_terms()
    metadata_field_list = [
        "tissue",
        "disease",
        "development_stage",
        "organism",
        "sex",
        "assay",
        "self_reported_ethnicity",
    ]
    metadata_field_list = [
        field_name
        for field_name in metadata_field_list
        if field_name in aea.enricher_manager.anndata.obs.columns
    ]
    gg.add_metadata_nodes(metadata_fields=metadata_field_list)
    if bitmap_output_dir is not None:
        logger.info(f"Building cluster bitmaps in {bitmap_output_dir}...")
        try:
            build_cluster_bitmaps(aea, gg, bitmap_output_dir)
        except Exception:
            logger.exception("Bitmap build failed; continuing with RDF graph save.")
    gg.save_rdf_graph(file_name=output_rdf_path)
    logger.info(f"RDF graph has been generated for {anndata_file_path}...")

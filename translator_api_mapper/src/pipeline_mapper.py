from gene_node_unifier.gene_node_unifier import gene_node_unifier
from pr_uniprot_id_swapper.pr_uniprot_id_swapper import pr_uniprot_id_swapper
from uniprot_ensembl_mapper.uniprot_ensembl_mapper import uniprot_ensembl_mapper

# Swap CL PR term URIs with UniProtKB dbxref values CL_KG#53
pr_uniprot_id_swapper()
# Link from Proteins (uniprot) to Genes (Ensembl) CL_KG#73
uniprot_ensembl_mapper()
# Unify Genes (Ensembl) with NCBIGene nodes
gene_node_unifier()

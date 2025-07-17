from gene_node_unifier.gene_node_unifier import gene_node_unifier
from pr_uniprot_id_swapper.pr_uniprot_id_swapper import pr_uniprot_id_swapper
from uniprot_gene_mapper.uniprot_gene_mapper import uniprot_gene_mapper

# Swap CL PR term URIs with UniProtKB dbxref values CL_KG#53
pr_uniprot_id_swapper()
# Link from Proteins (uniprot) to Genes (Ensembl) CL_KG#73
uniprot_gene_mapper()
# Unify Genes (Ensembl) with NCBIGene nodes
gene_node_unifier()

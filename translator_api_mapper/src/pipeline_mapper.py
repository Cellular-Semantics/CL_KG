from gene_node_unifier.gene_node_unifier import gene_node_unifier
from uniprot_ensembl_mapper.uniprot_ensembl_mapper import uniprot_ensembl_mapper

# Links from Proteins (uniprot) to Genes (Ensembl) CL_KG#73
uniprot_ensembl_mapper()
# Unifies Genes (Ensembl) with NCBIGene nodes
gene_node_unifier()

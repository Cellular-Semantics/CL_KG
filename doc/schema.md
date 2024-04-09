Status: Draft

# OWL/RDF to Neo4j Schema

Defined in [documentation of owl2neo library](https://github.com/OBASKTools/neo4j2owl?tab=readme-ov-file#entities).

## Nested cell sets:

Cell sets are individuals representing author category cell type annotations. 

 (c1)-[:INSTANCEOF]-(:Cluster {} ) 
 (c1)-[:subcluster_of]-(c2)

If cells sets have indentical membership, they are unified into a single node.
 
## Cell sets to Cell ontology terms

(c:Cluster)-[:consists_predominantly_of]->(cl:Cell:Class)

## Cell sets to standard CxG metadata (apart from cell ontlogy terms)

(c:Cluster)-[:CxG_metadata_key { percent_overlap: <float> }]-(x)

Where precent_overlap = percent of cells in anocell_set that are in cell

e.g. 
(c:Cluster)-[:tissue { percent_overlap: 50.5 }]->(:Class { label: 'cornea', short_form: 'UBERON_'})

## Maker sets




Status: Draft

# OWL/RDF to Neo4j Schema

Defined in [documentation of owl2neo library](https://github.com/OBASKTools/neo4j2owl?tab=readme-ov-file#entities).

## Nested cell sets:

Cell sets are individuals representing author category cell type annotations.

```cypher
 (c1)-[:INSTANCEOF]-(:Cluster { label: 'cluster' } )
// Where one cell set subsumes another it is represented as
 (c1)-[:subcluster_of]->(c2) 
```

'cluster' (PCL:0010001) # This should be improved!
subcluster_of [RO:0015003](https://www.ebi.ac.uk/ols4/ontologies/ro/properties/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252FRO_0015003).  This relation is transitive, a transitive reduction step is needed in generating the graph.

All cell sets representing author cell type annotations MUST be present, however, if cell sets have identical membership, they are unified into a single node. Configuration specifies an order of preference for which annotation will become rdfs:label if nodes are unified.  All other names are stored with their original keys.

TBD: Should we also represent overlaps between author annotations.  These could use RO:overlaps and record percent_overlap on the edge (should think about how this fits with confusion matrix generation)
 
## Cell sets to Cell ontology terms

The cell_type fields in the CELLxGENE schema also define cell sets 

Where there is a 1:1 relationship between a cell set defined by a cell_type annotation and one represented by an author annotation, this is represented by:

```cypher
(c:Cluster)-[:composed_primarily_of]->(cl:Cell:Class) 
```

'composed primarily of' ([RO:0002473](https://www.ebi.ac.uk/ols4/ontologies/ro/properties/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252FRO_0002473))

Where a cell set defined by a cell_type annotation doesn't map to single cell set defined by author category annotation, but subsumes >1 of these, this is represented as:

(c:Cluster)-[:TBD]->(cl:Cell:Class)

Note - this is relatively rare in CxG.

**All cell ontology terms MUST be represented.** 

## Cell sets to standard CxG metadata (apart from cell ontlogy terms)

(c:Cluster)-[:CxG_metadata_key { percent_overlap: <float> }]-(x)

Where precent_overlap = percent of cells in anocell_set that are in cell

e.g. 
(c:Cluster)-[:tissue { percent_overlap: 50.5 }]->(:Class { label: 'cornea', short_form: 'UBERON_'})

## Markers/marker sets

TBA




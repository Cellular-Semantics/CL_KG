**Status**: Draft

# OWL/RDF to Neo4j Schema

Defined in [documentation of owl2neo library](https://github.com/OBASKTools/neo4j2owl?tab=readme-ov-file#entities).

## Nested cell sets:

Cell sets are individuals representing author category cell type annotations.

```cypher
 (c1)-[:INSTANCEOF]-(:Cluster { label: 'cluster' } ) // 'cluster' (PCL:0010001) # This should be improved!
// Where one cell set subsumes another it is represented as
 (c1)-[:subcluster_of]->(c2) subcluster_of [RO:0015003](https://www.ebi.ac.uk/ols4/ontologies/ro/properties/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252FRO_0015003)
```
subcluster_of is transitive, so a transitive reduction step MUST be used in generating the graph.

All cell sets representing author cell type annotations MUST be present, however, if cell sets have identical membership, they are unified into a single node. Configuration specifies an order of preference for which annotation will become rdfs:label if nodes are unified.  All other names are stored with their original keys.

TBD: Should we also represent overlaps between author annotations.  These could use RO:overlaps and record percent_overlap on the edge (should think about how this fits with confusion matrix generation)
 
## Cell sets to Cell ontology terms

The cell_type fields in the CELLxGENE schema also define cell sets.

**All cell ontology terms MUST be represented.** 

Where there is a 1:1 relationship between a cell set defined by a cell_type annotation and one represented by an author annotation, this is represented by:

```cypher
(c:Cluster)-[:composed_primarily_of]->(cl:Cell:Class) 
```

'composed primarily of' ([RO:0002473](https://www.ebi.ac.uk/ols4/ontologies/ro/properties/http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252FRO_0002473))

Where a cell set defined by a cell_type annotation doesn't map to single cell set defined by author category annotation, but subsumes >1 of these, this is represented as:

TBD

proposal 1:

```cypher
(c:Cluster)-[:cluster_overlaps]->(cl:Cell:Class) // Relations needs to be requested.  Use built-in for now
```

proposal 2: 

Generate a cluster (cell set) node for the cell_type & relate this as above. One advantage of this is that it allows for CxG metadata to be consistently attached to an author annotation node.

Note - this is relatively rare in CxG.


## Cell sets to standard [CxG metadata](https://github.com/chanzuckerberg/single-cell-curation/blob/main/schema/5.0.0/schema.md) (apart from cell ontlogy terms)

```cypher
(c:Cluster)-[:CxG_metadata_key { percent_overlap: <float> }]-(x)
```

Where percent_overlap = percent of cells in cell_set defined by author annotation that are in cell_set defined by metadata annotation.

e.g.
```cypher
(c:Cluster)-[:tissue { percent_overlap: 50.5 }]->(:Class { label: 'cornea', short_form: 'UBERON_'})
```

Above properties are reprented as OBASK builtin

## Markers/marker sets

TBA




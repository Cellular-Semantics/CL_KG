#  Pipeline code for building a cell type knowledge graph

Components:
* Hierarchies of nested cell sets defined by author category cell type annotations, combined with CL annotation.
* The Cell Ontology and interlinked OBO ontologies - initial emphasis on GO & Pro.
* Gene/Protein Annotations to GO terms that:
   * Are supported by strong experimental evidence
   * Cover mouse and human genes (we may consider adding other mammals)
   * Are directly linked to CL terms or are closely linked via some defined pattern (e.g. if a cell type has a cellular component, then we should also pull annotations to terms for assembly and maintenance of that cell type).
* Sources of assertions about cell type markers:   LLMs, CL, GO, CAS.
* Curated information about cell types and the processes they are involved in derived from LLM-based piplines.
* In all cases, we will capture which publications support/sources support assertions.
* Standard model for linking Gene/Protein/Transcript IDs.  TBD.  Initially at least I suggest aggregating to single Neo4J nodes and using APs.
* For all markers found via any route, validate against annotated data using CxG Census query & storing sumamry statistics - mean, median, variance, entropy? This information can be stored in edge annotation.

Pipelines:
* Pandasaurus extracts cell sets linked to CL terms following standard schemas
* Python script to QuickGO API to extract relevant GO annotations

Use cases:
 * Mining CxG for missing CL terms and CL annotations (Cypher queries to be defined)
 * Cell Type marker query service
   *  Define Cypher queries
   *  Build API
   *  Build LLM query layer
 *  Input to ML algorithms assigning cell type. This is experimental. We need partners early enough in development do guide and avoid making poor choices.  It is probably worth being aware of existing options for generating embeddings (e.g. node2vec)

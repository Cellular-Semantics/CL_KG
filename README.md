# Access

An experimental version of this knowledge graph is available at http://172.27.24.69:7474/browser/.  Read-only access is credential-less and is currently restricted to within the Sanger VPN.

#  Pipeline code for building a cell type knowlege graph

Components:
* [x] Hierarchies of nested cell sets defined by author-category cell type annotations, combined with CL annotation.  These are currently sourced from CellXGene.
* [x] The Cell Ontology and interlinked OBO ontologies - initial emphasis on GO, Uberon and Pro
* [ ] Standard model for linking Gene/Protein/Transcript IDs.  TBD.  Initially at least I suggest aggregating to single Neo4J nodes and using APs. 
* Gene/Protein Annotations to GO terms that:
   * Are supported by strong experimental evidence
   * Cover mouse and human genes (we may consider adding other mammals)
   * Are directly linked to CL terms or are closely linked via some defined pattern (e.g. if a cell type has a cellular component, then we should also pull annotations to terms for assembly and maintenance of that cell type).
* Sources of assertions about cell type markers (In all cases, we will capture which publications support/sources support assertions):
   * LLMs queries
   * [ ] CL (We have any directly linked markers at present, but there are many in comments that we could mine).
   * CAS
   * Curated marker sources (we should include xrefs back to DBs so that they can be acknowledged/linked-to results):
       * [ ] HubMap ASCT+B (To check - can we reliably download these from their APIs or should mine more directly)
       * [ ] [CellMarker 2.0]([url](http://bio-bigdata.hrbmu.edu.cn/CellMarker/)) - downloadable table of marker, cell type (CL), tissue (Uberon) Paper
       * [ ] https://panglaodb.se/ - cell type is free text but easily mapped to CL.
       * [ ] Organ specific DBs e.g. [LungMap](https://www.lungmap.net/research/cell-cards/?cell_cards_id=LMCC0000000026)
* Curated information about cell types and the processes they are involved in derived from LLM-based piplines.
* [ ] For all markers found via any route, validate against annotated data using CxG Census query & storing sumamry statistics - mean, median, variance, entropy? This information can be stored in edge annotation.

Pipelines:
* [x] Pandasaurus extracts cell sets linked to CL terms following standard schemas
    - Note - we can also take advantage of an alternative route via CAS (CAS-Tools can import from CxG and export (with additional annotations) to RDF)
* [ ] Python script to QuickGO API to extract relavant GO annotations

Use cases:
 * Mining CxG for missing CL terms and CL annotations (Cypher queries to be defined)
 * Cell Type marker query service
   *  Define Cypher queries
   *  Build API
   *  Build LLM query layer
 *  Input to ML algorithms assigning cell type. This is experimental. We need partners early enough in development do guide and avoid making poor choices.  It is probably worth being aware of existing options for generating embeddings (e.g. node2vec)

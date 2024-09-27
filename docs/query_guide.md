## KG query guide

### Other relevant docs

[CL_KG user stories, schema and roadmap](https://docs.google.com/document/d/1CIvy_NV1poK1wK-lY9E_sksOIRDxMyyBc-ZZLzD8OrM/edit#heading=h.vq3lz7r6domf)

[OWL-2-NEO mapping](https://github.com/OBASKTools/neo4j2owl/blob/master/README.md#owl-2-el---neo4j-mapping-direct-existentials)

### Access

Refer to the [Access guide](access_guide.md) for instructions on accessing the Cell Type Knowledge Graph.

### Useful MATCH clauses

**Clause to find author annotated cell sets for a specific dataset:**

```cypher
MATCH (cc:Cell_cluster)-[:has_source]->(ds) 
WHERE ds.publication = ['https://doi.org/10.1038/s41586-021-03852-1']
```

Alternatively, one could use ds.title or ds.collection as a restriction, these take dataset titles and colleciton URLs for CxG respectively.

**Clause to match cell sets to CL annotations:**

```cypher
MATCH p=(c:Class:Cell)<-[:composed_primarily_of]-(s1:Cell_cluster)
```

**Using CL structure to find annotations with some specified cell type or its subclasses**

```cypher
MATCH p=(superclass:Cell)<-[:SUBCLASSOF*0..]-(c:Class:Cell)<-[:composed_primarily_of]-(s1:Cell_cluster)
```


**Clause to finds subsets (subclusters) of cell sets**

```cypher
MATCH (s1)<-[:subcluster_of*..]-(s2)
```

**Clause to find the proportion of cells in a cell set from specific tissue**

```cypher
MATCH (cc:Cell_cluster {label: 'Enterocyte' )-[t:tissue]->(anat)
RETURN t.percentage, anat.label, anat.short_form
```

## Putting it all together

**Query to find the proportion of cells by tissue on a specific annotation**

This was motivated by finding an annotation:

Author_cell_type: 'Enterocyte'; cell_type: 'enterocyte of colon'

Question: Does the tissue origin justify annotating this as a cell type of the colon.

```cypher
MATCH (cc:Cell_cluster)-[:has_source]->(ds { publication: ['https://doi.org/10.1038/s41586-021-03852-1']}) 
MATCH p=(c:Cell { label: 'enterocyte of colon'})<-[:composed_primarily_of]
-(cc:Cell_cluster{label: 'Enterocyte'})-[t:tissue]->(anat)
RETURN anat.label, t.percentage[0]
```
anat.label | t.percentage[0]
-- | --
ileum | 58.96
duodenum | 25.89
large intestine | 1.21
jejunum | 6.06
mesenteric lymph node | 0.01
small intestine | 6.96
colon | 0.9

Conclusion:  >97% if cells are from the small intestine so this annotation is incorrect.


**For a specific dataset, find author annotations that are more granular than the CxG CL annotation**

```cypher
MATCH (s1:Cell_cluster)-[:has_source]->(ds) 
WHERE ds.publication = ['https://doi.org/10.1038/s41586-021-03852-1']
MATCH p=(c:Class:Cell)<-[:composed_primarily_of]-(s1)<-[:subcluster_of*..]-(s2)
RETURN p
```

**For all datasets, find author annotations taht are more granular than the CxG CL annotation, and where the CL term is a leaf node**

```cypher
MATCH p=(c:Class:Cell)<-[:composed_primarily_of]-(s1)<-[:subcluster_of*..]-(s2) where not (c)<-[:SUBCLASSOF]-() return p
```


**Find leaf node CL terms with nested cell sets underneath**


Example results from Sikemma:

<img width="878" alt="image" src="https://github.com/cellannotation/CAS-LinkML/assets/112839/4a90d9dd-40ac-4bb7-9af7-c238b6abb7ba">

** Query to find General term used for specific class**

e.g. T-Cell here:

<img width="483" alt="image" src="https://github.com/cellannotation/CAS-LinkML/assets/112839/9587df72-668a-4b3f-a4b4-7a06bfe34e50">

```cypher
MATCH p=(c:Class:Cell)<-[:composed_primarily_of]-(s1:Cluster) where (c)<-[:SUBCLASSOF]-() and not (s1)<-[:subcluster_of]-() return p
```

<img width="349" alt="image" src="https://github.com/cellannotation/CAS-LinkML/assets/112839/67226c10-9915-405f-bd85-5969baca9f08">

c.label | s1.label | More specific term needed* | CL term to use | Notes
-- | -- | -- | -- |  -- 
serous secreting cell | SMG serous (nasal) | Y |  | SMG = submucosal gland.  We have no nasal SMG serous term.
tracheobronchial goblet cell | Goblet (subsegmental) | ? |  |  Need to check if could be more precise | 
tracheobronchial serous cell | SMG serous (bronchial) | n  | serous secreting cell of bronchus submucosal gland
bronchial goblet cell | Goblet (bronchial) | n | | 
CD4-positive, alpha-beta T cell | CD4 T cells | n | | 
mucus secreting cell | SMG mucous | n | mucus secreting cell of bronchus submucosal gland | |
ciliated columnar cell of tracheobronchial tree | Multiciliated (non-nasal) | n
dendritic cell | Migratory DCs | y || 
lung macrophage | Interstitial Mph perivascular | y || "perivascular macrophage" is currently brain specific!  We also have lung interstitial macrophage
plasmacytoid dendritic cell | Plasmacytoid DCs | n || 
smooth muscle cell | SM activated stress response | y? || 
epithelial cell of alveolus of lung | AT0 | Y || 
fibroblast | Subpleural fibroblasts | Y || 
tracheobronchial smooth muscle cell | Smooth muscle | N || 
epithelial cell of lower respiratory   tract | pre-TB secretory | Y | | TB = tracheobronchial
CD8-positive, alpha-beta T cell | CD8 T cells | N || 
T cell | T cells proliferating | N || 
conventional dendritic cell | DC1 | N || 
brush cell of trachebronchial tree | Tuft | N || 

*quick assessment - may not be 100% acurate

## Author Cell Type annotations more granular than CL

### Numbers of author annotations (in loaded datasets) with no direct mapping to a CL term

```cypher
MATCH (s2:Cell_cluster) where NOT (s2)-[:composed_primarily_of]->(:Cell) 
return count (distinct s2)
// = 21953
;
```

###  Numbers of author annotations (in loaded datasets) with mapping to CL broader than 1:1

```cypher
MATCH p=(c:Class:Cell)<-[:composed_primarily_of]-(s1)<-[:subcluster_of*..]-(s2)  
where NOT (s2)-[:composed_primarily_of]->(:Cell) return count (distinct s2)
;
```

#### Example - Elementaite - Gut

```cypher
MATCH (s1:Cell_cluster)-[:has_source]->(ds) 
WHERE ds.publication = ['https://doi.org/10.1038/s41586-021-03852-1']
MATCH p=(c:Class:Cell)<-[:composed_primarily_of]-(s1)<-[:subcluster_of*..]-(s2) 
WHERE NOT (s2)-[:composed_primarily_of]->(:Cell)
RETURN p
;
```

#### All new or unannotated cell types

```cypher
MATCH (c:Class:Cell)<-[:composed_primarily_of]-(s1)<-[:subcluster_of*..]-(s2:Cell_cluster) 
WHERE NOT (s2)-[:composed_primarily_of]->(:Cell) 
AND NOT (toLower(c.label_rdfs[0])=toLower(s2.label)) 
AND NOT (s2.label STARTS WITH 'ns_') // BUG workaround
AND NOT (s2.label =~ ".+[0-9]$") // ignore anything ending in a number
AND NOT (toLower(s2.label) =~ ".*unknown.*") // ignore anything with unknown in name
AND NOT (toLower(s2.label) =~ ".*unclassified.*") // ignore anything with unclassified in name
AND NOT (toLower(s2.label) =~ ".*other.*") // ignore anything with other in name
MATCH (s2:Cell_cluster)-[t:tissue]->(:Class) //-[:part_of|SUBCLASSOF*0..]->(anat:Class) // Optional restrict to system 
WHERE toFloat(t.percentage[0]) > 5 // and anat.label_rdfs[0] = 'intestine' // Optional restrict to system
MATCH (s2)-[d:disease]->(normal:Disease { label: 'normal'}) where toFloat(d.percentage[0]) > 5
MATCH (s2)-[:has_source]-(ds:Dataset)
RETURN DISTINCT c.label_rdfs[0] as broad_CL_ann, s2.label as unmappped_author_ann, collect(distinct (anat.label)) as source_tissues, toFloat(d.percentage[0]) as percent_normal, ds.title as dataset_title, ds.citation as dataset_details
ORDER BY ds.title, broad_CL_ann
;
```

 => 3978

AMICA auto-annotator can be used to make a first pass mapping & flag potential missing cell types.

#### Attemped break down by system:

```cypher
MATCH (c:Class:Cell)<-[:composed_primarily_of]-(s1)<-[:subcluster_of*1..]-(s2:Cell_cluster) 
WHERE NOT (s2)-[:composed_primarily_of]->(:Cell) 
AND NOT (toLower(c.label_rdfs[0])=toLower(s2.label)) 
AND NOT (s2.label STARTS WITH 'ns_') // BUG workaround
AND NOT (s2.label =~ ".+[0-9]$") // ignore anything ending in a number - assume there are T-types
AND NOT (toLower(s2.label) =~ ".*unknown.*") // ignore anything with unknown in name
AND NOT (toLower(s2.label) =~ ".*unclassified.*") // ignore anything with unclassified in name
AND NOT (toLower(s2.label) =~ ".*other.*") // ignore anything with other in name
MATCH (s2:Cell_cluster)-[t:tissue]->(anat:Class)-[:part_of|SUBCLASSOF*0..]->(sys:Class)-[:SUBCLASSOF]->(as:Class { label: 'anatomical system'})// AND anat.label_rdfs[0] = 'intestine' // Optional restrict to by anatomy
WHERE toFloat(t.percentage[0]) > 5 
MATCH (s2)-[d:disease]->(normal:Disease { label: 'normal'}) where toFloat(d.percentage[0]) > 5
MATCH (s2)-[:has_source]-(ds:Dataset)
RETURN  count (distinct s2.label), sys.label
;
```

Not perfect but gives a rough idea of systems with large numbers of new or unannotated cell types
 
* 1367	"nervous system"
* 44	"ventricular system of central nervous system"
* 112	"respiratory system"
* 209	"digestive system"
* 48	"cardiovascular system"

### Marker validation with GO

#### Few cases of GO validation markers for NS-Forest

```cypher
MATCH p=(g:Gene)<-[:has_part]-(ms:Class)<-[:has_characterizing_marker_set|has_marker_set]
-(:Cell_cluster)-[]->(c:Cell)-[rg]-(go:Class)<-[]-(:Protein)<-[]-(g) 
WHERE 'Biological_process' in labels(go) OR 'Cellular_component' in labels(go)
return c.label as cell_type, g.label as gene, rg.label as cell_go_rel, go.label, ms.label,
       CASE
         WHEN id(c) = id(startNode(rg)) THEN 'cell -> go'
         ELSE 'go -> cell'
       END AS direction
;
``` 

#### Much larger number if valildations from other marker sources:

```cypher
MATCH p=(g:Gene)<-[]->(c:Cell)-[rg]-(go:Class)<-[]-(:Protein)<-[]-(g) 
WHERE 'Biological_process' in labels(go) OR 'Cellular_component' in labels(go)
return c.label as cell_type, g.label as gene, rg.label as cell_go_rel, go.label,
       CASE
         WHEN id(c) = id(startNode(rg)) THEN 'cell -> go'
         ELSE 'go -> cell'
       END AS direction
ORDER BY cell_type, gene
;
```

### General marker queries 

#### NS-Forest to cell types

```cypher
MATCH p=(g:Gene)<-[:has_part]-(:Class)<-[hm:has_characterizing_marker_set|has_marker_set]-(c:Cell)
return count (distinct c) as cell_types, count (distinct g) as genes, count (distinct hm) as marker_sets
;
```

#### NS-Forest to clusters:

```cypher
MATCH p=(g:Gene)<-[:has_part]-(:Class)<-[hm:has_characterizing_marker_set|has_marker_set]-(c:Cell_cluster)
return count (distinct c) as cell_types, count (distinct g) as genes, count (distinct hm) as marker_sets
;
```

### Single markers by source:

```cypher
MATCH p=(g:Gene)<-[hm:has_marker]->(c:Cell)
return count (distinct c) as cell_types, count (distinct g) as genes, 
count (distinct hm) as marker_assertions
;
```

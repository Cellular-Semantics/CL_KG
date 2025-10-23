## Marker schema doc

Date: 251022

AFAIK there are currently 3 sources of markers loaded:

- CxG - single reference, every marker has an individual markers score in a context + one marker score with no context
- CellMark - Many references.  No marker scores.  Every marker may have a context.
- NS-Forest - A few references. Groups of markers have an F-beta score and a context.

Schema:
```cypher
MATCH p=(g:Gene)<-[hp:has_part]-(ms:Class)
  <-[hm:has_characterizing_marker_set]-(c:Cell)
MATCH q = (ms)-[:context]->(:Class) 
RETURN p,q
```

CxG + CellMark are aggregated on context

e.g. 

```cypher
MATCH p=(g:Gene)<-[hp:has_part]-(ms:Class)
  <-[hm:has_characterizing_marker_set]-(c:Cell) 
WHERE c.label = 'B cell' AND g.label = 'MS4A1'
OPTIONAL MATCH (ms)-[:context]->(con:Class) 
RETURN c.label, g.label, hp.marker_score, con.label, ms.references
```

=>

c.label | g.label | hp.marker_score | con.label | ms.references
-- | -- | -- | -- | --
B cell | MS4A1 | [1.6859511] | kidney | [PMID:34783463,https://doi.org/10.1101/2023.10.30.563174,...]
B cell | MS4A1 | [1.47596] | esophagus | [https://doi.org/10.1101/2023.10.30.563174,PMID:31892341]
B cell | MS4A1 | null | decidua | [PMID:34168655]
B cell | MS4A1 | null | bone marrow | [PMID:33846355,https://doi.org/10.1101/2023.10.30.563174 ...]
B cell | MS4A1 | [2.4003873] | exocrine gland | [https://doi.org/10.1101/2023.10.30.563174]
B cell | MS4A1 | [1.9412133] | null | [PMID:32690901,https://doi.org/10.1101/2023.10.30.563174, ...]

(ref lists trimmed)
`con.label is null` = no context in CxG or CellMark

Source: 

ROBOT templates: https://github.com/Cellular-Semantics/CellMark/tree/main/src/templates/cl_kg
Sources are from external links
CellMark pulled by: https://github.com/Cellular-Semantics/CellMark/blob/main/src/scripts/cellmarker_marker_template_genenrator.py
CELLxGENE data pulled by: https://github.com/Cellular-Semantics/CellMark/blob/main/src/scripts/cellxgene_marker_template_generator.py



NS-Forest comes from CellMark.  Aggregation is set there

```cypher
MATCH p=(g:Gene)<-[hp:has_part]-(ms:Class)
  <-[hm:has_characterizing_marker_set]-(c:Cell) 
WHERE ms.F4beta_score is not null
OPTIONAL MATCH (ms)-[:context]->(con:Class) 
RETURN distinct c.label, collect(g.label), 
                ms.F4beta_score , con.label, ms.references
```

c.label | collect(g.label) | ms.F4beta_score | con.label | ms.references
-- | -- | -- | -- | --
cycling pulmonary alveolar type 2 cell | [PRC1,TOP2A,PEG10] | [0.61] | null | null
cycling alveolar macrophage | [NUSAP1,PCLAF,RRM2,UBE2C] | [0.26] | null | null
CCL3-positive alveolar macrophage | [CXCL5,TNIP3] | [0.67] | null | null
metallothionein-positive alveolar   macrophage | [HMOX1,HPGD] | [0.41] | null | null
lung interstitial macrophage | [STAB1,FCGR2B,F13A1 (Hsap)] | [0.46] | null | null
respiratory tract suprabasal cell | [SERPINB4,KRT15,TNC] | [0.62] | null | null


Notes - no context or references - would need to be updated in CellMark to fix
Minor: F-beta_score name mangled (maybe via URLencode followed by special character stripping?)

### Aggregating queries

```cypher
MATCH p=(g:Gene)<-[hp:has_part]-(ms:Class)<-[hm:has_characterizing_marker_set]-(c:Cell) 
OPTIONAL MATCH (c)-[]-(go:Class)-[]-(:Protein)<-[:produces]-(g)
 WHERE ('Biological_process' in labels(go)) OR ('Cellular_component') in labels(go) 
RETURN c.label, g.label, 
size(apoc.coll.toSet(apoc.coll.flatten(collect(distinct ms.references)))) as refs,
 round(apoc.coll.avg(apoc.coll.flatten(collect(hp.marker_score)))) as average_marker_score,
size(collect(distinct go.label))
ORDER BY average_marker_score DESC
```
We could use this to => reports for markers by cell type with options to rank
by number of refs, marker score, number of supporting GO terms...

Optionally specify a context.

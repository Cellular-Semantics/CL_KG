# Dataset Curation Guidelines for Loading and File Placement

This guide outlines the process for curating datasets and specifies where to place the curation 
files for proper loading. By following these guidelines, you ensure datasets are prepared correctly 
for integration and that the files are stored in the appropriate directories for seamless access 
and management.

## Curation Process: Steps for Preparing Datasets

This section describes the necessary steps to format, validate, and prepare datasets for loading 
into the system, ensuring they meet the required standards.

### Dataset Curation Guidelines

These guidelines are designed to help curators prepare datasets for the pipeline. Below, each 
column in the curated CSV is explained with example values to guide curators in correctly 
filling in the necessary data taken from https://cellxgene.cziscience.com/collections/9b02383a-9358-4f0f-9795-a891ec523bcc.

---

### Columns and Guidelines

1. **Dataset (individual datasets within larger group):**
   - **Description**: The specific name of the dataset being curated within a larger dataset group.
   - **Example**: "Single cell transcriptional and chromatin accessibility profiling redefine 
     cellular heterogeneity in the adult human kidney - ATACseq"
   
2. **Full name dataset (top of page):**
   - **Description**: The full descriptive name of the dataset that should be used for 
     documentation and display.
   - **Example**: "Single cell transcriptional and chromatin accessibility profiling redefine 
     cellular heterogeneity in the adult human kidney"
   
3. **CxG Link:**
   - **Description**: The CellxGene link to access the dataset.
   - **Example**: "https://cellxgene.cziscience.com/e/13a027de-ea3e-432b-9a5e-6bc7048498fc.cxg/"
   
4. **h5ad link:**
   - **Description**: The direct link to the `.h5ad` data file of the dataset.
   - **Example**: "https://datasets.cellxgene.cziscience.com/dabd979f-cc50-4526-81f3-8bc6c673ca36.h5ad"
   
5. **Reference_DOI:**
   - **Description**: The DOI reference for the associated publication(s) for the dataset.
   - **Example**: "DOI: 10.1038/s41467-021-22368-w"
   
6. **Bionetworks reference:**
   - **Description**: Indicate whether the dataset has a reference within the Bionetworks repository.
   - **Example**: "T" (True)
   
7. **Standard category present? (T/F):**
   - **Description**: Flag indicating whether standard categories are present in the dataset.
   - **Example**: "T" (True)
   
8. **Standard category cell_type present? (T/F):**
   - **Description**: Flag indicating whether the standard category for cell type is present in 
     the dataset.
   - **Example**: "T" (True)
   
9. **Author Category Cell Type Field Name:**
   - **Description**: This column shows the name of the field as it appears in the Dataset 
     Explorer UI. It indicates which specific field within the dataset corresponds to a certain 
     category, such as "cell type" or other annotations. Fields marked as `Cell types` in the 
     `Content` column play a key role in graph generation using the `pandasaurus_cxg` library, which 
     is employed in the data pipeline.
   - **Example**: "author_cell_type"
   
10. **Content:**
    - **Description**: This column indicates whether the field is used for cell type annotations 
      or for other dataset annotations (e.g., Cell type or Other).
    - **Example**: "Cell types"
    
11. **Value type(s):**
    - **Description**: This column specifies if the values in the dataset are represented in full 
      names or as abbreviations.
    - **Example**: "abbreviations"
    
12. **Notes:**
    - **Description**: Any additional notes or comments regarding the dataset.
    - **Example**: "Muto et al. (2021) Nat Commun"
    
13. **Study Short Name:**
    - **Description**: The shortened name or acronym of the study associated with the dataset.
    - **Example**: "Muto et al. (2021) Nat Commun"
    
14. **CxG Dataset Collection X:**
    - **Description**: The CellxGene link to the collection where the dataset is stored.
    - **Example**: "https://cellxgene.cziscience.com/collections/9b02383a-9358-4f0f-9795-a891ec523bcc"
    
15. **Is the dataset Normal or Normal/Diseased:**
    - **Description**: Indicates whether the dataset is of normal samples or includes both 
      normal and diseased samples.
    - **Example**: "Normal"
    
16. **Stage:**
    - **Description**: The biological stage of the samples in the dataset, such as adult, fetal, etc.
    - **Example**: "Adult"

---

## General Tips for Curators:
- Ensure that fields marked as `Cell types` in the `Content` column are correctly paired with 
  appropriate `Author Category Cell Type Field Name`, as these pairs are crucial for graph 
  generation in the data pipeline using the `pandasaurus_cxg` library.
- Ensure all links (CxG and h5ad) are correct and accessible.
- Use consistent naming for datasets across related entries.
- Double-check flags (T/F) to ensure they correctly reflect the presence of specific categories.
- Fill out fields such as `Study Short Name` and `Notes` with proper references to aid in 
  documentation and user clarity.

By following these guidelines, curators can ensure that datasets are correctly formatted and 
ready for integration into the pipeline.


## File Placement: Where to Store Curation Files

This section provides guidance on the correct directory structure and file locations for placing 
curated datasets to ensure they are properly recognized and accessible during the loading process.

In the pipeline, curated CSV files are stored in the `curated_data` folder. When the pipeline is 
run, these CSV files are automatically converted into a YAML file named `cxg_author_cell_type.yml` 
and placed in the `config` folder. The YAML file maps the CxG links to the corresponding 
`author_cell_type_list` fields, which are essential for processing.

Example of the YAML format:

```yaml
- CxG_link: https://datasets.cellxgene.cziscience.com/03af5481-a0b6-426c-86b4-9127ada17b53.h5ad
  author_cell_type_list:
  - author_cell_type
  - author_cluster_label
- CxG_link: https://datasets.cellxgene.cziscience.com/080f9be4-0f94-48cb-a82f-db53df1542ff.h5ad
  author_cell_type_list:
  - author_cluster_name
  - author_cell_type
  - author_cell_type

```

The CxG links in the YAML file are then used to download datasets into the `dataset` folder. 
Finally, the `pandasaurus_cxg` library is used to generate RDF graphs, which are stored in the 
`graph` folder for further use in the pipeline.
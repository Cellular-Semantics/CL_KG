import pytest

from pull_anndata import get_dataset_dict, get_dataset_id_from_link

UUID = "a12ccb9b-4fbe-457d-8590-ac78053259ef"


@pytest.mark.parametrize(
    "link",
    [
        f"https://cellxgene.cziscience.com/e/{UUID}.cxg/",
        f"https://cellxgene.cziscience.com/e/{UUID}.cxg",
        f"https://datasets.cellxgene.cziscience.com/{UUID}.h5ad",
    ],
)
def test_get_dataset_id_from_link_extracts_uuid(link):
    assert get_dataset_id_from_link(link) == UUID


@pytest.mark.parametrize("link", ["", None, "https://cellxgene.cziscience.com/e/not-a-uuid.cxg/"])
def test_get_dataset_id_from_link_rejects_links_without_uuid(link):
    with pytest.raises(ValueError):
        get_dataset_id_from_link(link)


def test_get_dataset_dict_keys_by_matrix_id():
    config = [
        {
            "CxG_link": f"https://cellxgene.cziscience.com/e/{UUID}.cxg/",
            "download_url": "https://datasets.cellxgene.cziscience.com/x.h5ad",
            "author_cell_type_list": ["celltype"],
            "dataset_id": "ds",
            "dataset_version_id": "dsv",
        }
    ]
    assert get_dataset_dict(config) == {
        UUID: {
            "author_cell_type_list": ["celltype"],
            "download_url": "https://datasets.cellxgene.cziscience.com/x.h5ad",
            "dataset_id": "ds",
            "dataset_version_id": "dsv",
        }
    }

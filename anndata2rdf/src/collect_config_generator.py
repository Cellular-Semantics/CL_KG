import yaml


def parse_cxg_link_from_yaml(yaml_file):
    # Load YAML data from file
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)

    # Extract CxG_link from YAML data
    cxg_links = [entry.get('CxG_link', None) for entry in data]

    return cxg_links


def generate_owl_file_url(cxg_link):
    if cxg_link:
        # Extract the UUID from the CxG_link
        uuid = cxg_link.split("/")[-1].split(".")[0]

        # Generate the owl file URL
        owl_file_url = f"file:///out/local_ontologies/{uuid}.owl"
        return owl_file_url
    else:
        return None


def write_to_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)


if __name__ == "__main__":
    # Path to the YAML file
    yaml_file_path = "config/cxg_author_cell_type.yaml"
    # Path to the output file
    output_file_path = "mahmut.txt"

    # Parse the CxG_link from YAML
    cxg_links = parse_cxg_link_from_yaml(yaml_file_path)

    owl_file_urls = [generate_owl_file_url(cxg_link) for cxg_link in cxg_links]

    # Write the owl file URLs to the output file
    with open(output_file_path, 'w') as file:
        for owl_file_url in owl_file_urls:
            if owl_file_url:
                file.write(owl_file_url + '\n')
        print(f"Generated owl file URLs written to {output_file_path}")


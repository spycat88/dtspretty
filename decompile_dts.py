import sys, argparse
import yaml
import json
import re
from dts_parser import parse_dts_content
from parse_dts_symbols import parse_dts_symbols
from dereference_phandles import dereference_phandles

def load_yaml_rules(yaml_content):
    """Load dereferencing rules from YAML content."""
    rules = yaml.safe_load(yaml_content)

    # Normalize rules to ensure all entries are dictionaries
    for key, value in rules.items():
        if isinstance(value, list):
            # Treat a list directly as a struct
            rules[key] = {"struct": value}
        elif isinstance(value, dict):
            # Ensure the dictionary has 'patterns' or 'struct'
            rules[key].setdefault("patterns", [])
        else:
            raise ValueError(f"Unexpected rule format for key '{key}': {value}")
    
    return rules


def generate_restored_dts(dts):
    """Generate DTS file content from the restored structure."""
    # Implement DTS generation logic
    # For simplicity, we return a JSON string in this example
    return json.dumps(dts, indent=2)

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore references in decompiled DTS")
    parser.add_argument("-r", "--rules", help="Rules file (YAML)")
    parser.add_argument(metavar="/path/to/decompiled.dts", dest="src", help="input file")
    args = parser.parse_args()

    # Load DTS content (decompiled)
    with open(args.src, "r") as f:
        dts_content = f.read()

    # Load YAML rules
    with open(args.rules, "r") as f:
        yaml_content = f.read()

    # Load symbols and rules
    phandle_to_path, path_to_symbol = parse_dts_symbols(dts_content)
    rules = load_yaml_rules(yaml_content)

    # Parse DTS into a structured format (JSON or dictionary)
    dts = parse_dts_content(dts_content)

    # Restore references
    restored_dts = dereference_phandles(dts, phandle_to_path, path_to_symbol, rules)

    # Generate output DTS
    output_dts = generate_restored_dts(restored_dts)
    print(output_dts)

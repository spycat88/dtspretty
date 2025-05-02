import re

def dereference_phandles(dts, phandle_to_path, path_to_symbol, rules):
    """Restore references in the DTS structure following rules."""
    def resolve_property(prop, value):
        """Resolve property references based on rules."""
        for rule_name, rule in rules.items():
            patterns = rule.get("patterns", [])
            if any(re.match(pattern, prop) for pattern in patterns):
                # If property matches a rule, process it using the rule's logic
                return resolve_struct(value, rule_name)
        # If no matching rule, return the value as-is
        return value

    def resolve_struct(value, rule_name):
        """Resolve a property value based on its rule."""
        if not isinstance(value, list):
            value = [value]  # Ensure value is a list for processing
        resolved = []
        i = 0
        while i < len(value):
            if isinstance(value[i], int):  # If the value is a phandle
                # Resolve phandle to path
                ref_path = phandle_to_path.get(value[i])
                if not ref_path:
                    # If phandle doesn't resolve, append as is
                    resolved.append(hex(value[i]))
                    i += 1
                    continue

                # Resolve path to symbolic name (if any)
                ref_symbol = f"&{path_to_symbol.get(ref_path, ref_path.lstrip('/'))}"

                # Find the referenced node in the DTS by path
                ref_node = find_node_by_path(dts, ref_path)
                if not ref_node:
                    # If the referenced node is not found, just add the reference and continue
                    resolved.append([ref_symbol])
                    i += 1
                    continue

                # Get the "#clock-cells" (or equivalent) value from the referenced node
                clock_cells_property = f"#{rule_name}-cells"
                clock_cells = ref_node.get(clock_cells_property, 0)

                # Group the reference and the next 'clock_cells' items
                group = [ref_symbol] + value[i + 1 : i + 1 + clock_cells]
                resolved.append(group)

                # Skip the processed items
                i += 1 + clock_cells
            else:
                # If not a phandle, just add the value
                resolved.append(value[i])
                i += 1
        return resolved

    def find_node_by_path(dts, path):
        """Recursively find a node in the DTS by its path."""
        if not path:
            return None
        parts = path.strip("/").split("/")
        current_node = dts
        for part in parts:
            if isinstance(current_node, dict) and part in current_node:
                current_node = current_node[part]
            else:
                return None
        return current_node

    def process_node(node):
        """Recursively process a node."""
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, dict):
                    process_node(value)
                elif isinstance(value, list):
                    # Only process lists if the property matches a rule
                    node[key] = resolve_property(key, value)
                else:
                    node[key] = value

    process_node(dts)
    return dts


if __name__ == "__main__":
    # Example DTS content as a dictionary
    dts = {
        "clock-controller@ff2b0000": {
            "clocks": [0x01, 0x02, 1]
        },
        "xin24m": {
            "#clock-cells": 0,
            "phandle": 0x01
        },
        "clock-controller@ff2bc000": {
            "#clock-cells": 1,
            "phandle": 0x02
        }
    }

    # Phandle-to-Path dictionary
    phandle_to_path = {
        0x01: "/xin24m",
        0x02: "/clock-controller@ff2bc000"
    }

    # Path-to-Symbol dictionary
    path_to_symbol = {
        "/xin24m": "AAA",
        "/clock-controller@ff2bc000": "BBB"
    }

    # Rules for dereferencing
    rules = {
        "clock": {
            "patterns": ["^clocks$"]
        }
    }

    # Apply dereferencing
    restored_dts = dereference_phandles(dts, phandle_to_path, path_to_symbol, rules)

    # Print the result
    import json
    print(json.dumps(restored_dts, indent=2))

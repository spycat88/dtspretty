import re, sys

def dereference_phandles(dts, phandle_to_path, path_to_symbol, rules):
    """Restore references in the DTS structure following rules."""
    def resolve_property(prop, value):
        """Resolve property references based on rules."""
        for rule_name, rule in rules.items():
            patterns = rule.get("patterns", [])
            if any(re.search(pattern, prop) for pattern in patterns):
                # If property matches a rule, process it using the rule's logic
                return resolve_struct(value, rule_name, rule)
        # If no matching rule, return the value as-is
        return [value]

    def resolve_struct(value, rule_name, rule):
        """Resolve a property value based on its rule."""
        if not isinstance(value, list):
            value = [value]  # Ensure value is a list for processing
        resolved = []
        i = 0
        static_struct = rule.get('struct', None)
        while i < len(value):
            if static_struct:
                tmp = []
                for j in static_struct:
                    if i >= len(value):
                        continue
                    if j == 'ref':
                        ref_path = phandle_to_path.get(value[i])
                        ref_symbol = f"&{path_to_symbol.get(ref_path, ref_path.lstrip('/'))}"
                        tmp.append(ref_symbol)
                    elif j == 'd':
                        tmp.append(str(value[i]))
                    elif j == 'x':
                        tmp.append(hex(value[i]))
                    else:
                        tmp.append(str(value[i]))
                    i += 1
                resolved.append(tmp)
                continue
                
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
                while type(clock_cells) == list:
                    clock_cells = clock_cells[0]

                # Extract the data cells (pin number and flags for GPIO)
                data_cells = value[i + 1 : i + 1 + clock_cells]

                # Handle GPIO flags: resolve 0 to GPIO_ACTIVE_HIGH and 1 to GPIO_ACTIVE_LOW
                if rule_name == 'gpio' and clock_cells >= 2:
                    flags_index = clock_cells - 1
                    flags_value = data_cells[flags_index]
                    if flags_value == 0:
                        data_cells[flags_index] = "GPIO_ACTIVE_HIGH"
                    elif flags_value == 1:
                        data_cells[flags_index] = "GPIO_ACTIVE_LOW"

                # Group the reference and the next 'clock_cells' items
                group = [ref_symbol] + data_cells
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
                elif isinstance(value, str):
                    node[key] = [f'"{s}"' for s in value.split('\\0')]
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

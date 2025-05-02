def parse_dts_symbols(dts):
    """
    Parse the DTS structure and return two dictionaries:
    - phandle_to_path: Maps phandle values to corresponding paths exactly as in __symbols__ (starting with a slash).
    - path_to_symbol: Maps paths (from __symbols__) to corresponding symbolic names.
    """
    phandle_to_path = {}
    path_to_symbol = {}

    # Extract paths and symbols from __symbols__
    symbols = dts.get("__symbols__", {})
    for symbol, path in symbols.items():
        # Ensure path starts with a slash
        path_to_symbol[path] = symbol

    def process_node(node, path=""):
        """Recursively process each node in the DTS structure."""
        if not isinstance(node, dict):
            return

        # Look for phandle and map it to the corresponding path
        if "phandle" in node:
            phandle = node["phandle"]

            # Match the path from `__symbols__` if possible
            resolved_path = next(
                (symbol_path for symbol_path in path_to_symbol if path == symbol_path),
                "/"+f"{path}".strip("/")  # Ensure fallback path starts with a slash
            )
            phandle_to_path[phandle] = resolved_path

        # Recurse into child nodes
        for key, value in node.items():
            if isinstance(value, dict):
                process_node(value, f"{path}/{key}".strip("/"))

    process_node(dts)
    return phandle_to_path, path_to_symbol


if __name__ == "__main__":
    # Example DTS as a dictionary
    dts = {
        "xin24m": {
            "phandle": 0x01
        },
        "clock-controller@ff2b0000": {
            "phandle": 0x03,
            "subnode": {
                "phandle": 0x04,
             }
        },
        "clock-controller@ff2bc000": {
            "phandle": 0x02
        },
        "__symbols__": {
            "xin24m": "/xin24m",
            "cru": "/clock-controller@ff2b0000",
            "pmucru": "/clock-controller@ff2bc000"
        }
    }

    phandle_to_path, path_to_symbol = parse_dts_symbols(dts)

    import json
    print("phandle_to_path:")
    print(json.dumps(phandle_to_path, indent=2))
    print("\npath_to_symbol:")
    print(json.dumps(path_to_symbol, indent=2))

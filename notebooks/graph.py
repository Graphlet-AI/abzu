import marimo

__generated_with = "0.14.17"
app = marimo.App(width="medium")

with app.setup:
    # Initialization code that runs before all other cells
    import os
    from collections import defaultdict

    import graphistry
    import matplotlib.pyplot as plt
    import networkx as nx
    import numpy as np
    import pandas as pd
    import seaborn as sns

    sns.set_theme(style="white", context="poster")

    GRAPHISTRY_USERNAME = os.getenv("GRAPHISTRY_USERNAME")
    GRAPHISTRY_PASSWORD = os.getenv("GRAPHISTRY_PASSWORD")


@app.cell
def _():
    # May need to re-run if you step away for a while
    graphistry.register(
        api=3,
        username=GRAPHISTRY_USERNAME,
        password=GRAPHISTRY_PASSWORD,
        server="hub.graphistry.com",
    )
    return


@app.cell
def _():
    # Configuration for Graphistry
    GRAPHISTRY_PARAMS = {
        "play": 500,
        "pointOpacity": 0.7,
        "edgeOpacity": 0.3,
        "edgeCurvature": 0.3,
        "showArrows": True,
        "gravity": 0.15,
        "showPointsOfInterestLabel": False,
        "labels": {
            "shortenLabels": False,
        },
    }
    FAVICON_URL = "https://graphlet.ai/assets/icons/favicon.ico"
    LOGO = {
        "url": "https://rjurneyopen.s3.amazonaws.com/Graphlet-AI-Logo-Transparent.png",
        "dimensions": {"maxWidth": 100, "maxHeight": 100},
    }
    return FAVICON_URL, GRAPHISTRY_PARAMS, LOGO


@app.cell
def _():
    #
    # Graphistry has trouble with null values - this can break a visualization when coloring by value. This utility imputes nulls.
    #

    # Function to check if a value should be replaced
    def needs_replacement(value):
        """Is it None, 'null' or null string?"""
        return value is None or value == "null" or value == ""

    def clean_graph(G):
        """Impute empty networkx graph properties with 0s"""
        G_copy = G.copy()

        # Profile the types in fields
        field_type_count = defaultdict(lambda: defaultdict(int))
        for node, attrs in G_copy.nodes(data=True):
            for key, value in attrs.items():
                field_type_count[key][type(value)] += 1

        # Take the most common type for each
        prop_types = {}
        for property, type_count in field_type_count:
            top_type_pair = max(type_count.items(), key=lambda x: x[1])
            top_type = top_type_pair[0]
            prop_types[property] = top_type

        for node, attrs in G_copy.nodes(data=True):
            for key, value in attrs.items():
                if (prop_types[key] == str) and needs_replacement(value):
                    G_copy.nodes[node][key] = "0"

        return G_copy

    return (needs_replacement,)


@app.cell
def _():
    node_df = pd.read_parquet("data/refined_knowledge_graph/nodes.parquet")

    # Convert ticker struct to string for Graphistry compatibility
    if "ticker" in node_df.columns:
        node_df["ticker"] = node_df["ticker"].apply(
            lambda x: x.get("symbol", "") if isinstance(x, dict) else ""
        )

    # Count source_uuids but keep as list
    if "source_uuids" in node_df.columns:
        node_df["source_uuid_count"] = node_df["source_uuids"].apply(
            lambda x: len(x) if x is not None else 0
        )
    if "match_skip_history" in node_df.columns:
        node_df["match_skip_history"] = node_df["match_skip_history"].apply(
            lambda x: ", ".join(map(str, x)) if x is not None else ""
        )

    node_df
    return (node_df,)


@app.cell
def _():
    relationship_df = pd.read_parquet("data/refined_knowledge_graph/edges.parquet")

    # Flatten nested country struct into separate columns
    if "country" in relationship_df.columns:
        country_df = pd.json_normalize(relationship_df["country"].dropna())
        if not country_df.empty:
            country_df = country_df.add_prefix("country_")
            country_df.index = relationship_df["country"].dropna().index
            relationship_df = relationship_df.join(country_df)
        relationship_df = relationship_df.drop(columns=["country"])

    # Convert array columns to strings for Graphistry compatibility
    if "products" in relationship_df.columns:
        relationship_df["products"] = relationship_df["products"].apply(
            lambda x: ", ".join(x) if x is not None else ""
        )
    if "technologies" in relationship_df.columns:
        relationship_df["technologies"] = relationship_df["technologies"].apply(
            lambda x: ", ".join(x) if x is not None else ""
        )

    relationship_df
    return (relationship_df,)


@app.cell
def _(relationship_df):
    relationship_df.groupby("relationship").count()["src"]
    return


@app.cell
def _(relationship_df):
    edge_df = relationship_df[relationship_df.src.notnull() & relationship_df.dst.notnull()].copy()

    # Fill NaN values for Graphistry compatibility
    # Handle numeric columns separately to avoid mixed types
    for col in edge_df.columns:
        if edge_df[col].dtype in ["float64", "int64", "float32", "int32"]:
            edge_df[col] = edge_df[col].fillna(0)
        else:
            edge_df[col] = edge_df[col].fillna("")

    # Ensure amount column is numeric (it may have mixed types)
    if "amount" in edge_df.columns:
        edge_df["amount"] = pd.to_numeric(edge_df["amount"], errors="coerce").fillna(0)

    edge_df.count()
    return (edge_df,)


@app.cell
def _(edge_df, node_df):
    # 1. Create a map `uuid_to_int`.
    all_uuids = pd.concat([node_df["uuid"], edge_df["src"], edge_df["dst"]]).unique()
    uuid_to_int = {uuid: i for i, uuid in enumerate(all_uuids)}

    # Add an integer ID to the company dataframe
    node_df["id"] = node_df["uuid"].map(uuid_to_int)

    # Replace src and dst in edge_df with integer IDs
    edge_df["src"] = edge_df["src"].map(uuid_to_int)
    edge_df["dst"] = edge_df["dst"].map(uuid_to_int)

    # 2. Create the graph with integer IDs
    G = nx.from_pandas_edgelist(
        edge_df, source="src", target="dst", edge_attr=True, create_using=nx.DiGraph()
    )
    return (G,)


@app.cell
def _(G, node_df):
    # Add nodes with ALL attributes from the company dataframe
    # set_index is important here so the keys of the dict are the node IDs
    node_attributes_df = node_df[node_df["id"].notnull()].copy()
    node_attributes_df = node_attributes_df.set_index("id")

    # Fill NaN values appropriately for Graphistry
    # Handle numeric columns separately to avoid mixed types
    for col in node_attributes_df.columns:
        if node_attributes_df[col].dtype in ["float64", "int64", "float32", "int32"]:
            node_attributes_df[col] = node_attributes_df[col].fillna(0)
        else:
            node_attributes_df[col] = node_attributes_df[col].fillna("")

    node_attributes = node_attributes_df.to_dict("index")
    nx.set_node_attributes(G, node_attributes)

    print(node_attributes[0])
    return (node_attributes,)


@app.cell
def _(FAVICON_URL, G, GRAPHISTRY_PARAMS, LOGO):
    g = (
        graphistry.bind(
            source="src",
            destination="dst",
            node="id",
            point_title="name",
            point_label="name",
        )
        .scene_settings(
            edge_opacity=0.4,
        )
        .addStyle(
            page={
                "title": "Time Period Sample",
                "favicon": FAVICON_URL,
            },
            logo=LOGO,
        )
        .settings(
            url_params=GRAPHISTRY_PARAMS,
            height=800,
        )
    )
    g.plot(G)
    return (g,)


@app.cell
def _(G, edge_df, g, node_attributes):
    # G.add_nodes_from takes an iterable of (node, attribute_dict)
    G.add_nodes_from(node_attributes.items())

    # Add edges from the edge dataframe
    # .values creates a numpy array of [src, dst] pairs

    G.add_edges_from(
        [
            (row["src"], row["dst"], row.drop(["src", "dst"]).to_dict())
            for _, row in edge_df.iterrows()
        ]
    )

    print(f"Original graph has {G.number_of_nodes():,} nodes and {G.number_of_edges():,} edges.")

    # Drop disconnected nodes
    G.remove_nodes_from(list(nx.isolates(G.to_undirected())))

    print(
        f"Without isolates graph has {G.number_of_nodes():,} nodes and {G.number_of_edges():,} edges."
    )

    # Display a summary of the created graph
    print(G)
    g.plot(G)
    return


@app.cell
def _(G):
    def describe_graph(G):
        """Given a networkx Graph, describe its key properties."""

        print(f"Number of nodes: {G.number_of_nodes():,}")
        print(f"Number of edges: {G.number_of_edges():,}")

        # Compute various network properties
        degrees = [deg for _, deg in nx.degree(G)]
        avg_degree = sum(degrees) / G.number_of_nodes()
        median_degree = np.median(degrees)
        print(f"Mean degree: {avg_degree:,.3f}")
        print(f"Median degree: {median_degree:,.3f}")

        components = nx.connected_components(G.to_undirected())
        largest_component = max(components, key=len)
        print(
            f"Number of connected components: {nx.number_connected_components(G.to_undirected()):,}"
        )
        print(f"Size of the largest component: {len(largest_component):,}")

        # If the network is directed, you can also print the following
        if G.is_directed():
            print(
                f"Number of strongly connected components: {nx.number_strongly_connected_components(G):,}"
            )
            print(
                f"Number of weakly connected components: {nx.number_weakly_connected_components(G):,}"
            )

        avg_clustering = nx.average_clustering(G)
        median_clustering = np.median(list(nx.clustering(G).values()))
        print(f"Mean clustering coefficient: {avg_clustering:.6f}")
        print(f"Median clustering coefficient: {median_clustering:.6f}")

        # try:
        #     avg_shortest_path_length = nx.average_shortest_path_length(G)
        #     print(f"Average shortest path length: {avg_shortest_path_length}")
        # except nx.NetworkXError:
        #     print("Graph is not connected, average shortest path length is not defined.")

    describe_graph(G)
    return


@app.cell
def _(G):
    # Get connected components and their sizes
    components = nx.connected_components(G.to_undirected())
    component_sizes = [len(c) for c in components]

    # Increase figure size
    plt.figure(figsize=(10, 6))

    # Use seaborn to create the histogram
    sns.histplot(component_sizes, kde=True, bins=40, log_scale=True)
    plt.title("Histogram of Connected Component Sizes - Finance Graph")
    plt.xlabel("Component Size")
    plt.ylabel("Count")
    plt.show()
    return


@app.cell
def _(G):
    clustering_coeffs = nx.clustering(G)

    for c_node, clustering_coeff in clustering_coeffs.items():
        G.nodes[c_node]["clustering_coefficient"] = clustering_coeff
    return


@app.cell
def _(G, needs_replacement):
    G_clean = G.copy()

    # Profile the types in fields
    field_type_count = defaultdict(dict)
    for node, attrs in G_clean.nodes(data=True):
        for key, value in attrs.items():
            type_val = str(type(value))
            if (
                key in field_type_count
                and type_val in field_type_count[key]
                and field_type_count[key][type_val]
            ):
                field_type_count[key][type_val] += 1
            else:
                field_type_count[key][type_val] = 1

    # Take the most common type for each
    prop_types = {}
    for property, type_count in field_type_count.items():
        top_type_pair = max(type_count.items(), key=lambda x: x[1])
        top_type = top_type_pair[0]
        prop_types[property] = top_type

    for node, attrs in G_clean.nodes(data=True):
        for key, value in attrs.items():
            if (prop_types[key] == str) and needs_replacement(value):
                G_clean.nodes[node][key] = 0
    return (G_clean,)


@app.cell
def _(G_clean):
    G_clean.nodes(data=True)
    return


@app.cell
def _(FAVICON_URL, GRAPHISTRY_PARAMS, G_clean):
    g2 = (
        graphistry.bind(
            source="src",
            destination="dst",
            node="id",
            point_title="name",
            point_label="name",
        )
        .scene_settings(
            edge_opacity=0.4,
        )
        .addStyle(
            page={
                "title": "Graphlet Capital Graph",
                "favicon": FAVICON_URL,
            },
            # logo=LOGO,
        )
        .settings(
            url_params=GRAPHISTRY_PARAMS,
            height=800,
        )
    )
    g2.plot(G_clean)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

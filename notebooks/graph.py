import marimo

__generated_with = "0.14.17"
app = marimo.App(width="medium")


@app.cell
def _():
    import os
    from collections import defaultdict
    from typing import Union

    import graphistry
    import matplotlib.pyplot as plt
    import networkx as nx
    import numpy as np
    import pandas as pd
    import seaborn as sns
    from networkx import DiGraph, Graph

    sns.set_theme(style="white", context="poster")
    return (
        DiGraph,
        Graph,
        Union,
        defaultdict,
        graphistry,
        np,
        nx,
        os,
        pd,
        plt,
        sns,
    )


@app.cell
def _(os):
    GRAPHISTRY_USERNAME = os.getenv("GRAPHISTRY_USERNAME")
    GRAPHISTRY_PASSWORD = os.getenv("GRAPHISTRY_PASSWORD")
    return GRAPHISTRY_PASSWORD, GRAPHISTRY_USERNAME


@app.cell
def _(GRAPHISTRY_PASSWORD, GRAPHISTRY_USERNAME, graphistry):
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
        "url": "https://graphlet.ai/assets/Branding/Graphlet%20AI.svg",
        "dimensions": {"maxWidth": 100, "maxHeight": 100},
    }
    return FAVICON_URL, GRAPHISTRY_PARAMS, LOGO


@app.cell
def _(DiGraph, Graph, Union, defaultdict):
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
                    G_copy.nodes[node][key] = 0
        return G_copy

    return (clean_graph, needs_replacement)


@app.cell
def _(pd):
    company_df = pd.read_parquet("data/knowledge_graph/companies.parquet")
    company_df
    return (company_df,)


@app.cell
def _(pd):
    product_df = pd.read_parquet("data/knowledge_graph/products.parquet")
    product_df
    return


@app.cell
def _(pd):
    technology_df = pd.read_parquet("data/knowledge_graph/technologies.parquet")
    technology_df
    return


@app.cell
def _(pd):
    relationship_df = pd.read_parquet("data/knowledge_graph/relationships.parquet")
    relationship_df
    return (relationship_df,)


@app.cell
def _(relationship_df):
    relationship_df.groupby("relationship").count()["src"]
    return


@app.cell
def _(relationship_df):
    edge_df = relationship_df[relationship_df.src.notnull() & relationship_df.dst.notnull()]
    edge_df.count()
    return (edge_df,)


@app.cell
def _(edge_df):
    edge_df
    return


@app.cell
def _(company_df, edge_df, nx, pd):
    # 1. Create a map `uuid_to_int`
    all_uuids = pd.concat([company_df["uuid"], edge_df["src"], edge_df["dst"]]).unique()
    uuid_to_int = {uuid: i for i, uuid in enumerate(all_uuids)}

    # Add an integer ID to the company dataframe
    company_df["id"] = company_df["uuid"].map(uuid_to_int)

    # Replace src and dst in edge_df with integer IDs
    edge_df["src"] = edge_df["src"].map(uuid_to_int)
    edge_df["dst"] = edge_df["dst"].map(uuid_to_int)

    # 2. Create the graph with integer IDs
    G = nx.DiGraph()

    # Add nodes with attributes from the company dataframe
    # set_index is important here so the keys of the dict are the node IDs
    node_attributes = company_df[["id", "name", "description"]].set_index("id").to_dict("index")
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
    return (G,)


@app.cell
def _(G, np, nx):
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
def _(G, nx, plt, sns):
    # Get connected components and their sizes
    components = nx.connected_components(G.to_undirected())
    component_sizes = [len(c) for c in components]

    # Increase figure size
    plt.figure(figsize=(10, 6))

    # Use seaborn to create the histogram
    sns.histplot(component_sizes, kde=True, bins=30, log_scale=False)
    plt.title("Histogram of Connected Component Sizes")
    plt.xlabel("Component Size")
    plt.ylabel("Count")
    plt.show()
    return


@app.cell
def _():
    # clustering_coeffs = nx.clustering(G)

    # for c_node, clustering_coeff in clustering_coeffs.items():
    #     G.nodes[c_node]['clustering_coefficient'] = clustering_coeff

    return


@app.cell
def _(G, defaultdict, needs_replacement):
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
def _(FAVICON_URL, GRAPHISTRY_PARAMS, G_clean, LOGO, graphistry):
    g = (
        graphistry.bind(
            source="src",
            destination="dst",
            node="nodeid",
            point_title="name",
            point_label="name",
        )
        .scene_settings(
            edge_opacity=0.4,
        )
        .addStyle(
            page={
                "title": "Abzu Capital Graph",
                "favicon": FAVICON_URL,
            },
            logo=LOGO,
        )
        .settings(
            url_params=GRAPHISTRY_PARAMS,
            height=800,
        )
    )
    g.plot(G_clean)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()

import os
from collections import defaultdict

import graphistry
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import pyarrow as pa
import seaborn as sns

sns.set_theme(style="white", context="poster")

GRAPHISTRY_USERNAME = os.getenv("GRAPHISTRY_USERNAME")
GRAPHISTRY_PASSWORD = os.getenv("GRAPHISTRY_PASSWORD")

# May need to re-run if you step away for a while
graphistry.register(
    api=3,
    username=GRAPHISTRY_USERNAME,
    password=GRAPHISTRY_PASSWORD,
    server="hub.graphistry.com",
)
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


def safe_array_to_string(x):
    """Convert array/list/ndarray to comma-separated string, handling None and numpy arrays."""
    if x is None:
        return ""
    # Handle numpy arrays by converting to list first
    if isinstance(x, np.ndarray):
        x = x.tolist()
    if isinstance(x, (list, tuple)):
        return ", ".join(str(item) for item in x)
    return str(x)


def safe_dict_to_string(x):
    """Convert dict to string representation, handling None."""
    if x is None:
        return ""
    if isinstance(x, dict):
        # Convert dict to a readable string format
        return "; ".join(f"{k}={v}" for k, v in x.items() if v is not None)
    return str(x)


node_df = pd.read_parquet("data/refined_knowledge_graph/nodes.parquet")

# Flatten nested ticker struct into separate columns
if "ticker" in node_df.columns:
    # First, check if there are any non-null ticker values
    non_null_tickers = node_df["ticker"].dropna()
    if len(non_null_tickers) > 0:
        ticker_df = pd.json_normalize(non_null_tickers)
        if not ticker_df.empty:
            ticker_df = ticker_df.add_prefix("ticker_")
            ticker_df.index = non_null_tickers.index
            node_df = node_df.join(ticker_df)
    node_df = node_df.drop(columns=["ticker"])

# Convert array columns to strings for Graphistry compatibility
if "source_uuids" in node_df.columns:
    node_df["source_uuid_count"] = node_df["source_uuids"].apply(
        lambda x: len(x) if x is not None and hasattr(x, "__len__") else 0
    )
    node_df["source_uuids"] = node_df["source_uuids"].apply(safe_array_to_string)
if "match_skip_history" in node_df.columns:
    node_df["match_skip_history"] = node_df["match_skip_history"].apply(safe_array_to_string)

# Fill any remaining NaN values with empty strings for string columns
for n_col in node_df.select_dtypes(include=["object"]).columns:
    node_df[n_col] = node_df[n_col].fillna("")

node_df

relationship_df = pd.read_parquet("data/refined_knowledge_graph/edges.parquet")

# Flatten nested country struct into separate columns
if "country" in relationship_df.columns:
    # First, check if there are any non-null country values
    non_null_countries = relationship_df["country"].dropna()
    if len(non_null_countries) > 0:
        country_df = pd.json_normalize(non_null_countries)
        if not country_df.empty:
            country_df = country_df.add_prefix("country_")
            country_df.index = non_null_countries.index
            relationship_df = relationship_df.join(country_df)
    relationship_df = relationship_df.drop(columns=["country"])

# Convert array columns to strings for Graphistry compatibility (handles numpy arrays)
if "products" in relationship_df.columns:
    relationship_df["products"] = relationship_df["products"].apply(safe_array_to_string)
if "technologies" in relationship_df.columns:
    relationship_df["technologies"] = relationship_df["technologies"].apply(safe_array_to_string)

# Fill any remaining NaN values with empty strings for string columns
for r_col in relationship_df.select_dtypes(include=["object"]).columns:
    relationship_df[r_col] = relationship_df[r_col].fillna("")

relationship_df

relationship_df.groupby("relationship").count()["src"]

edge_df = relationship_df[relationship_df.src.notnull() & relationship_df.dst.notnull()].copy()

# Convert ALL columns to strings for Graphistry/Arrow compatibility
# Some columns (amount, percentage, country_gdp) are float64 with NaN values,
# which when mixed with strings cause Arrow conversion errors
for col in edge_df.columns:
    # Convert everything to string, handling NaN/None values
    edge_df[col] = edge_df[col].apply(lambda x: "" if pd.isna(x) else str(x))

# Fill NaN values for Graphistry compatibility
edge_df = edge_df.fillna("")

edge_df.count()

for c in node_df.columns:
    print("trying col", c)
    pa.Table.from_pandas(node_df[[c]])

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

G.nodes

# Add nodes with ALL attributes from the company dataframe
# set_index is important here so the keys of the dict are the node IDs
node_attributes_df = node_df[node_df["id"].notnull()].copy()
node_attributes_df = node_attributes_df.set_index("id")

# Fill NaN values appropriately for Graphistry
# node_attributes_df = node_attributes_df.fillna("")

node_attributes = node_attributes_df.to_dict("index")

# Add node attributes to the graph
nx.set_node_attributes(G, node_attributes)

# Also ensure all nodes have attributes (some nodes from edges may not be in node_df)
G.add_nodes_from(node_attributes.items())

# Add edges from the edge dataframe
# .values creates a numpy array of [src, dst] pairs

G.add_edges_from(
    [(row["src"], row["dst"], row.drop(["src", "dst"]).to_dict()) for _, row in edge_df.iterrows()]
)

print(f"Original graph has {G.number_of_nodes():,} nodes and {G.number_of_edges():,} edges.")

# Drop disconnected nodes
G.remove_nodes_from(list(nx.isolates(G.to_undirected())))

print(
    f"Without isolates graph has {G.number_of_nodes():,} nodes and {G.number_of_edges():,} edges."
)

# Display a summary of the created graph
print(G)

# Create Graphistry visualization object
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
            "title": "Knowledge Graph",
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
    print(f"Number of connected components: {nx.number_connected_components(G.to_undirected()):,}")
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

# Get connected components and their sizes
components = nx.connected_components(G.to_undirected())
component_sizes = [len(c) for c in components]

# Increase figure size
plt.figure(figsize=(10, 6))

# Use seaborn to create the histogram
sns.histplot(component_sizes, kde=True, bins=30, log_scale=True)
plt.title("Histogram of Connected Component Sizes - Finance Graph")
plt.xlabel("Component Size")
plt.ylabel("Count")
plt.show()

clustering_coeffs = nx.clustering(G)

for c_node, clustering_coeff in clustering_coeffs.items():
    G.nodes[c_node]["clustering_coefficient"] = clustering_coeff

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

G_clean.nodes(data=True)

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

import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
from pathlib import Path
import streamlit.components.v1 as components
import random
import itertools

# Function to load data
@st.cache_data
def load_data():
    df = pd.read_csv('Drug-Drug-Interaction.csv')
    df.dropna(inplace=True)
    return df

# Generate a random color
def generate_color():
    return "#" + ''.join([random.choice('0123456789ABCDEF') for i in range(6)])

# Network properties function
def get_network_properties(G):
    properties = {
        "Number of Drugs": G.number_of_nodes(),
        "Number of Interactions": G.number_of_edges(),
        "Diameter": nx.diameter(G) if nx.is_connected(G) else 'N/A (Graph not connected)',
        "Average Degree": round(float(sum(dict(G.degree()).values())) / G.number_of_nodes(),2)
    }
    return properties



# Function to find common interacting drugs
def find_common_interactors(df, drug_pair):
    drugA, drugB = drug_pair
    interactors_A = set(df[(df['DrugA'] == drugA) | (df['DrugB'] == drugA)]['DrugB'].unique()) | set(df[(df['DrugA'] == drugA) | (df['DrugB'] == drugA)]['DrugA'].unique())
    interactors_B = set(df[(df['DrugA'] == drugB) | (df['DrugB'] == drugB)]['DrugB'].unique()) | set(df[(df['DrugA'] == drugB) | (df['DrugB'] == drugB)]['DrugA'].unique())
    common_interactors = interactors_A.intersection(interactors_B)
    return common_interactors - {drugA, drugB}

# Read dataset
df_interact = load_data()

# Layout
st.title('Drug-Drug Interaction Network Dashboard')
st.markdown("Explore the interactions between different drugs and network properties.")

# Sidebar for drug selection
with st.sidebar:
    st.header("Drug Selection")
    drug_list = sorted(df_interact['DrugA'].unique())
    selected_drugs = st.multiselect('Select Drugs', drug_list)


# Main panel
if not selected_drugs:
    st.info('Select at least two drugs to display their common interacting drugs.')
elif len(selected_drugs) < 2:
    st.warning('Please select at least two drugs for interaction analysis.')
else:
    # Filter data
    df_select = df_interact[df_interact['DrugA'].isin(selected_drugs) | df_interact['DrugB'].isin(selected_drugs)]
    G = nx.from_pandas_edgelist(df_select, 'DrugA', 'DrugB')

    # Network graph
    drug_net = Network(height='600px', bgcolor='#222222', font_color='white')
    drug_net.from_nx(G)

    # Color assignment
    color_map = {drug: generate_color() for drug in selected_drugs}
    for node in drug_net.nodes:
        node['color'] = color_map.get(node['label'], '#FFFFFF')

    drug_net.repulsion(node_distance=600, central_gravity=0.05, spring_length=150, spring_strength=0.08, damping=0.85)

    # Save and display graph
    path = Path('html_files')
    path.mkdir(exist_ok=True)
    file_path = path / 'pyvis_graph.html'
    drug_net.save_graph(str(file_path))
    HtmlFile = open(file_path, 'r', encoding='utf-8')
    components.html(HtmlFile.read(), height=600)

    # Network properties
    with st.sidebar:
        st.header("Network Properties")
        properties = get_network_properties(G)
        for prop, value in properties.items():
            st.metric(label=prop, value=value)

    # Additional data insights (if applicable)
        # Display common interactors for each pair
    st.markdown('***')


    st.header("Common Interacting Drugs")
    tab_list = st.tabs([f"{pair[0]} and {pair[1]}" for pair in itertools.combinations(selected_drugs, 2)])

    for tab, pair in zip(tab_list, itertools.combinations(selected_drugs, 2)):
        with tab:
            common_interactors = find_common_interactors(df_interact, pair)
            if common_interactors:
                st.write(', '.join(common_interactors))
            else:
                st.write("No common interacting drugs found.")
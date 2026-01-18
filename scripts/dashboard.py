import os
from neo4j import GraphDatabase
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")

# Neo4j connection
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password123")

driver = GraphDatabase.driver(URI, auth=AUTH)

def run_query(query):
    with driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]

print("=" * 50)
print("US ROAD NETWORK DASHBOARD")
print("=" * 50)

# ============================================
# FETCH ALL DATA
# ============================================
print("\n[1/4] Fetching total intersections and roads...")
total_intersections = run_query("MATCH (i:Intersection) RETURN count(i) AS total")[0]['total']
total_roads = run_query("MATCH ()-[r:ROAD]->() RETURN count(r) AS total")[0]['total']
avg_degree = round((2 * total_roads) / total_intersections, 2)

print(f"   Total Intersections: {total_intersections:,}")
print(f"   Total Roads: {total_roads:,}")

print("\n[2/4] Fetching degree distribution...")
degree_query = """
MATCH (i:Intersection)
WITH i, COUNT { (i)-[:ROAD]-() } AS degree
RETURN degree, count(*) AS count
ORDER BY degree
"""
degree_df = pd.DataFrame(run_query(degree_query))

print("\n[3/4] Fetching top 10 most connected intersections...")
top10_query = """
MATCH (i:Intersection)
WITH i, COUNT { (i)-[:ROAD]-() } AS degree
RETURN i.id AS intersection_id, degree
ORDER BY degree DESC
LIMIT 10
"""
top10_df = pd.DataFrame(run_query(top10_query))

print("\n[4/4] Fetching intersection categories...")
categories_query = """
MATCH (i:Intersection)
WITH i, COUNT { (i)-[:ROAD]-() } AS degree
RETURN 
    CASE 
        WHEN degree = 1 THEN 'Dead End (1 road)'
        WHEN degree = 2 THEN 'Pass Through (2 roads)'
        WHEN degree = 3 THEN 'T-Junction (3 roads)'
        WHEN degree = 4 THEN 'Crossroad (4 roads)'
        ELSE 'Major Hub (5+ roads)'
    END AS category,
    count(*) AS count
ORDER BY count DESC
"""
categories_df = pd.DataFrame(run_query(categories_query))

# ============================================
#  DASHBOARD
# ============================================
print("\nCreating dashboard...")

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        '<b>Degree Distribution</b>',
        '<b>Top 10 Most Connected Intersections</b>',
        '<b>Intersection Types</b>',
        '<b>Key Insights</b>'
    ),
    specs=[
        [{"type": "bar"}, {"type": "bar"}],
        [{"type": "bar"}, {"type": "table"}]
    ],
    vertical_spacing=0.15,
    horizontal_spacing=0.1
)

# ============================================
# CHART 1: Degree Distribution (Clean Bar Chart)
# ============================================
degree_colors = {
    1: '#E74C3C',  # Red - Dead ends
    2: '#3498DB',  # Blue - Pass through
    3: '#2ECC71',  # Green - T-junction
    4: '#9B59B6',  # Purple - Crossroad
    5: '#F39C12',  # Orange - Major hub
    6: '#E67E22'   # Dark orange - Major hub
}
colors = [degree_colors.get(d, '#95A5A6') for d in degree_df['degree']]

fig.add_trace(
    go.Bar(
        x=degree_df['degree'],
        y=degree_df['count'],
        marker_color=colors,
        text=degree_df['count'].apply(lambda x: f'{x:,}'),
        textposition='outside',
        textfont=dict(size=12, color='#2C3E50'),
        hovertemplate='<b>Degree %{x}</b><br>Count: %{y:,}<extra></extra>'
    ),
    row=1, col=1
)

# ============================================
# CHART 2: Top 10 Intersections (Horizontal Bar)
# ============================================
top10_sorted = top10_df.sort_values('degree', ascending=True)

fig.add_trace(
    go.Bar(
        y=top10_sorted['intersection_id'].astype(str),
        x=top10_sorted['degree'],
        orientation='h',
        marker_color='#3498DB',
        text=top10_sorted['degree'],
        textposition='outside',
        textfont=dict(size=12, color='#2C3E50'),
        hovertemplate='<b>Intersection %{y}</b><br>Degree: %{x}<extra></extra>'
    ),
    row=1, col=2
)

# ============================================
# CHART 3: Intersection Types (Horizontal Bar)
# ============================================
category_colors = ['#3498DB', '#2ECC71', '#9B59B6', '#E74C3C', '#F39C12']
categories_sorted = categories_df.sort_values('count', ascending=True)

fig.add_trace(
    go.Bar(
        y=categories_sorted['category'],
        x=categories_sorted['count'],
        orientation='h',
        marker_color=category_colors,
        text=categories_sorted['count'].apply(lambda x: f'{x:,}'),
        textposition='outside',
        textfont=dict(size=12, color='#2C3E50'),
        hovertemplate='<b>%{y}</b><br>Count: %{x:,}<extra></extra>'
    ),
    row=2, col=1
)

# ============================================
# CHART 4: Key Insights Table
# ============================================
most_common_type = categories_df.loc[categories_df['count'].idxmax(), 'category']
most_common_pct = round(categories_df['count'].max() / total_intersections * 100, 1)

insights_data = [
    ['📍 Total Intersections', f'{total_intersections:,}'],
    ['🛣️ Total Roads', f'{total_roads:,}'],
    ['📊 Average Connections', f'{avg_degree} roads per intersection'],
    ['📈 Maximum Connections', f'{degree_df["degree"].max()} roads'],
    
]

fig.add_trace(
    go.Table(
        header=dict(
            values=['<b>Metric</b>', '<b>Value</b>'],
            fill_color='#2C3E50',
            font=dict(color='white', size=14),
            align='left',
            height=40
        ),
        cells=dict(
            values=[
                [row[0] for row in insights_data],
                [row[1] for row in insights_data]
            ],
            fill_color=[['#F8F9FA', '#FFFFFF'] * 3],
            font=dict(color='#2C3E50', size=13),
            align='left',
            height=35
        )
    ),
    row=2, col=2
)

# ============================================
# UPDATE LAYOUT
# ============================================
fig.update_layout(
    title={
        'text': '<b>US Road Network Analysis Dashboard</b><br>',
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 26, 'color': '#2C3E50'}
    },
    showlegend=False,
    height=900,
    width=1400,
    paper_bgcolor='#FFFFFF',
    plot_bgcolor='#FFFFFF',
    font=dict(family="Arial, sans-serif", size=12),
    margin=dict(t=120, b=60, l=80, r=80)
)

# Update axes
fig.update_xaxes(title_text="Degree (Number of Roads)", row=1, col=1, 
                 title_font=dict(size=12), tickfont=dict(size=11))
fig.update_yaxes(title_text="Number of Intersections", row=1, col=1,
                 title_font=dict(size=12), tickfont=dict(size=11))

fig.update_xaxes(title_text="Degree", row=1, col=2,
                 title_font=dict(size=12), tickfont=dict(size=11))
fig.update_yaxes(title_text="Intersection ID", row=1, col=2,
                 title_font=dict(size=12), tickfont=dict(size=11))

fig.update_xaxes(title_text="Number of Intersections", row=2, col=1,
                 title_font=dict(size=12), tickfont=dict(size=11))
fig.update_yaxes(title_text="", row=2, col=1, tickfont=dict(size=11))

# ============================================
# SAVE AND SHOW
# ============================================
output_path = os.path.join(REPORTS_DIR, "dashboard.html")
fig.write_html(output_path)
print(f"\n  Dashboard saved to: {output_path}")

fig.show()

driver.close()

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import nltk
from collections import Counter
import re

# Page config
st.set_page_config(
    page_title="ABC News Analysis",
    page_icon="📰",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .st-emotion-cache-1v0mbdj {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("📰 ABC News Analysis Dashboard")
st.markdown("---")

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    try:
        df = pd.read_csv('extracted_data.csv')
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def clean_date_format(date_str):
    """Convert date strings to standard format"""
    if pd.isna(date_str):
        return None
        
    # Clean unnecessary text
    date_str = re.sub(r'(at|ago|Updated|Published)', '', str(date_str)).strip()
    
    try:
        # Handle relative dates like "6h ago", "2d ago"
        if any(unit in date_str.lower() for unit in ['h ago', 'd ago', 'm ago']):
            value = int(re.findall(r'\d+', date_str)[0])
            unit = date_str[-4]  # h, d or m
            now = datetime.now()
            if unit == 'h':
                return now - timedelta(hours=value)
            elif unit == 'd':
                return now - timedelta(days=value)
            elif unit == 'm':
                return now - timedelta(minutes=value)
        
        # Try standard date formats
        return pd.to_datetime(date_str, format='mixed')
        
    except Exception as e:
        return None

def analyze_word_frequencies(text_series):
    """Analyze word frequencies in text"""
    words = []
    for text in text_series:
        if isinstance(text, str):
            words.extend(re.findall(r'\w+', text.lower()))
    
    # Remove stop words
    stop_words = set(nltk.corpus.stopwords.words('english'))
    words = [w for w in words if w not in stop_words and len(w) > 2]
    
    return Counter(words)

# Load data
df = load_data()

if df is not None:
    # Process dates
    df['published'] = df['published'].apply(clean_date_format)
    df = df.dropna(subset=['published'])
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Date range selector
    min_date = df['published'].min()
    max_date = df['published'].max()
    
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(max_date - timedelta(days=30), max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (df['published'].dt.date >= start_date) & (df['published'].dt.date <= end_date)
        filtered_df = df.loc[mask]
    else:
        filtered_df = df
    
    # Main content area with three columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Daily News Publication Count")
        daily_counts = filtered_df.groupby(filtered_df['published'].dt.date).size().reset_index()
        daily_counts.columns = ['date', 'count']
        
        fig_timeline = go.Figure()
        fig_timeline.add_trace(go.Scatter(
            x=daily_counts['date'],
            y=daily_counts['count'],
            mode='lines+markers',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=8)
        ))
        fig_timeline.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title="Date",
            yaxis_title="Number of Articles",
            template="plotly_white",
            hovermode='x unified'
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    with col2:
        st.subheader("👥 Top Authors")
        author_counts = filtered_df['author'].value_counts().head(10)
        author_df = pd.DataFrame({
            'Author': author_counts.index,
            'Articles': author_counts.values
        })
        fig_authors = px.bar(
            author_df,
            x='Articles',
            y='Author',
            orientation='h',
            template="plotly_white"
        )
        fig_authors.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_title="Number of Articles",
            yaxis_title="Author",
            yaxis={'categoryorder':'total ascending'}
        )
        st.plotly_chart(fig_authors, use_container_width=True)
    
    # Word frequency analysis
    st.markdown("---")
    st.subheader("🔤 Most Common Words in Headlines")
    
    word_freq = analyze_word_frequencies(filtered_df['headline'])
    top_words = dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:15])
    
    fig_words = px.bar(
        x=list(top_words.keys()),
        y=list(top_words.values()),
        template="plotly_white"
    )
    fig_words.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis_title="Word",
        yaxis_title="Frequency",
        xaxis={'categoryorder':'total descending'}
    )
    st.plotly_chart(fig_words, use_container_width=True)
    
    # Recent articles table
    st.markdown("---")
    st.subheader("📑 Recent Articles")
    
    recent_articles = filtered_df.sort_values('published', ascending=False).head(10)
    for _, article in recent_articles.iterrows():
        with st.expander(f"{article['headline']}", expanded=False):
            st.write(f"**Published:** {article['published'].strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**Author:** {article['author']}")
            if isinstance(article['description'], str):
                st.write(article['description'])
else:
    st.error("Failed to load data. Please check if the CSV file exists and is accessible.")

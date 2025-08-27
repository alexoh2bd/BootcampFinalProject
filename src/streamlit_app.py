"""
AI News Sentiment Analyzer - Streamlit Web Application
Interactive dashboard for analyzing sentiment of AI-related news
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import json
from api_handler import AINewsAnalyzer
import io


# Page configuration
st.set_page_config(
    page_title="AI News Sentiment Analyzer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style> 
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .positive { color: #28a745; }
    .negative { color: #dc3545; }
    .neutral { color: #6c757d; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_config():
    """Load configuration from config.json"""
    with open('config.json', 'r') as f:
        return json.load(f)

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def load_news_data(query, days, sources=None, model="TextBlob"):
    """Load and cache news data"""
    try:
        analyzer = AINewsAnalyzer()
        df = analyzer.get_ai_news_with_sentiment(query=query, days=days, sources=sources, model=model)
        return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)


def create_sentiment_distribution(df):
    """Create sentiment distribution pie chart"""
    if df.empty:
        return None
    
    sentiment_counts = df['sentiment_label'].value_counts()
    
    fig = px.pie(
        values=sentiment_counts.values,
        names=sentiment_counts.index,
        title="🎯 Sentiment Distribution",
        color_discrete_map={
            'positive': '#28a745',
            'negative': '#dc3545',
            'neutral': '#6c757d'
        }
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def create_source_analysis(df):
    """Create source analysis chart"""
    if df.empty:
        return None
    
    source_sentiment = df.groupby(['source', 'sentiment_label']).size().unstack(fill_value=0)
    source_sentiment = source_sentiment.loc[source_sentiment.sum(axis=1).nlargest(10).index]
    
    fig = px.bar(
        source_sentiment.reset_index(),
        x='source',
        y=['positive', 'negative', 'neutral'],
        title="📰 Sentiment by News Source (Top 10)",
        color_discrete_map={
            'positive': '#28a745',
            'negative': '#dc3545',
            'neutral': '#6c757d'
        }
    )
    
    fig.update_layout(
        xaxis_title="News Source",
        yaxis_title="Number of Articles",
        xaxis_tickangle=-45
    )
    
    return fig

def create_polarity_distribution(df, thresh: float):
    """Create sentiment polarity distribution"""
    if df.empty:
        return None
    
    fig = px.histogram(
        df,
        x='sentiment_polarity',
        nbins=30,
        title="📊 Sentiment Polarity Distribution",
        labels={'sentiment_polarity': 'Sentiment Polarity', 'count': 'Number of Articles'}
    )
    
    # Add vertical lines for sentiment boundaries
    fig.add_vline(x=thresh, line_dash="dash", line_color="green", annotation_text="Positive Threshold", annotation_position="top right")
    fig.add_vline(x=-thresh, line_dash="dash", line_color="red", annotation_text="Negative Threshold", annotation_position="top left")
    fig.add_vline(x=0, line_dash="dash", line_color="gray", annotation_text="Neutral", annotation_position="top")
    return fig


def main():
    # Header
    st.markdown("<h1 class='main-header'>🤖 AI News Sentiment Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("### Discover the sentiment trends in AI-related news from around the world")
    
    # Load configuration
    config = load_config()
    
    # Sidebar controls
    st.sidebar.header("🔧 Analysis Settings")
    
    # Query input
    query_options = config["search_queries"]
    
    selected_query = st.sidebar.selectbox(
        "📝 Search Topic:",
        options=query_options,
        index=0
    )
    
    custom_query = st.sidebar.text_input(
        "Or enter custom search:",
        placeholder="e.g., 'generative AI'"
    )

    model_query = st.sidebar.selectbox(
        "📝 Search a Sentiment Model:",
        options=config["model_options"],
        index=0
    )
    
    # Use custom query if provided
    final_query = custom_query if custom_query else selected_query
    
    # Time range (days)
    days = st.sidebar.slider(
        "📅 Days to analyze:",
        min_value=1,
        max_value=30,
        value=7,
        help="How many days back to search for news"
    )

    # Date range filter (optional, after data is loaded)
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Optional: Filter by Date Range")
    date_range = None
    
    # News sources from config
    news_sources = config["news_sources"]
    
    source_option = st.sidebar.selectbox(
        "📰 Source Category:",
        options=config["source_categories"],
        index=0
    )
    
    if source_option == "Tech Media":
        sources = news_sources["tech_media"]
    elif source_option == "General News":
        sources = news_sources["general_news"]
    elif source_option == "US News":
        sources = news_sources["us_news"]
    elif source_option == "Financial News":
        sources = news_sources["financial_news"]
    else:
        sources = None
    
    # Load data
    if st.sidebar.button("🚀 Analyze News", type="primary"):
        with st.spinner(f"Fetching and analyzing news about '{final_query}'..."):
            df, error = load_news_data(final_query, days, sources=sources, model=model_query)
            
            if error:
                st.error(f"Error loading data: {error}")
                st.stop()
            
            if df.empty:
                st.warning("No articles found. Try adjusting your search parameters.")
                st.stop()
            
            # Store results in session state
            st.session_state.df = df
            st.session_state.query = final_query
            st.session_state.days = days

    # ===== Display results if data is available =====
    if 'df' in st.session_state and not st.session_state.df.empty:
        df = st.session_state.df

        # Date range filter UI (if date column exists)
        if 'published_at' in df.columns:
            min_date = pd.to_datetime(df['published_at']).min().date()
            max_date = pd.to_datetime(df['published_at']).max().date()
            start_date, end_date = st.sidebar.date_input(
                "Select date range:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            # Filter DataFrame by date range
            mask = (pd.to_datetime(df['published_at']).dt.date >= start_date) & (pd.to_datetime(df['published_at']).dt.date <= end_date)
            df = df.loc[mask]
            if df.empty:
                st.warning("No articles found in the selected date range.")
                st.stop()

        # ===== Summary Metrics =====
        st.markdown("### 📊 Analysis Summary")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📰 Total Articles", len(df))
        with col2:
            avg_polarity = df['sentiment_polarity'].mean()
            delta_polarity = f"{avg_polarity:+.3f}"
            st.metric("🎭 Avg Sentiment", f"{avg_polarity:.3f}", delta_polarity)
        with col3:
            positive_pct = (len(df[df['sentiment_label'] == 'positive']) / len(df) * 100)
            st.metric("😊 Positive %", f"{positive_pct:.1f}%")
        with col4:
            unique_sources = df['source'].nunique()
            st.metric("📺 News Sources", unique_sources)


        # ===== Charts =====
        st.markdown("### 📈 Visual Analysis")
        col1, col2 = st.columns(2)

        # Sentiment Distribution
        dist_fig = create_sentiment_distribution(df)
        if dist_fig:
            st.plotly_chart(dist_fig, use_container_width=True, key="dist_fig")
            # Export buttons
            buf = io.BytesIO()
            dist_fig.update_layout(template="plotly_white")
            dist_fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')  # 设置白底
            try:
                dist_fig.write_image(buf, format="png", engine="kaleido")
            except RuntimeError:
                # Fallback if Chrome/Kaleido not available
                html_buf = io.StringIO()
                dist_fig.write_html(html_buf)
                buf = io.BytesIO(html_buf.getvalue().encode('utf-8'))
            st.download_button("📷 Download Distribution Chart as PNG", buf.getvalue(),
                            "distribution_chart.png", mime="image/png")
            st.download_button("🌐 Download Distribution Chart as HTML",
                            dist_fig.to_html().encode("utf-8"), "distribution_chart.html",
                            mime="text/html")

        # Source Analysis
        source_fig = create_source_analysis(df)
        if source_fig:
            st.plotly_chart(source_fig, use_container_width=True, key="source_fig")
            buf = io.BytesIO()
            source_fig.update_layout(template="plotly_white")
            source_fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')  # 白底
            try:
                source_fig.write_image(buf, format="png", engine="kaleido")
            except RuntimeError:
                # Fallback if Chrome/Kaleido not available
                html_buf = io.StringIO()
                source_fig.write_html(html_buf)
                buf = io.BytesIO(html_buf.getvalue().encode('utf-8'))
            st.download_button("📷 Download Source Chart as PNG", buf.getvalue(),
                            "source_chart.png", mime="image/png")
            st.download_button("🌐 Download Source Chart as HTML",
                            source_fig.to_html().encode("utf-8"), "source_chart.html",
                            mime="text/html")

        # Polarity Distribution
        polarity_fig = create_polarity_distribution(df, 0.1)
        if polarity_fig:
            st.plotly_chart(polarity_fig, use_container_width=True, key="polarity_fig")
            buf = io.BytesIO()
            polarity_fig.update_layout(template="plotly_white")
            polarity_fig.update_layout(plot_bgcolor='white', paper_bgcolor='white')  # 白底
            try:
                polarity_fig.write_image(buf, format="png", engine="kaleido")
            except RuntimeError:
                # Fallback if Chrome/Kaleido not available
                html_buf = io.StringIO()
                polarity_fig.write_html(html_buf)
                buf = io.BytesIO(html_buf.getvalue().encode('utf-8'))
            st.download_button("📷 Download Polarity Chart as PNG", buf.getvalue(),
                            "polarity_chart.png", mime="image/png")
            st.download_button("🌐 Download Polarity Chart as HTML",
                            polarity_fig.to_html().encode("utf-8"), "polarity_chart.html",
                            mime="text/html")

    
        # ===== Export CSV button =====
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Export Analysis as CSV",
            data=csv_data,
            file_name=f"ai_news_analysis_{st.session_state.query.replace(' ', '_')}.csv",
            mime='text/csv'
        )
    
    else:
        # Welcome message
        st.info("👋 Welcome! Configure your analysis settings in the sidebar and click 'Analyze News' to get started.")
        
        # Sample visualization or instructions
        st.markdown("""
        ### 🚀 How to Use:
        
        1. **Choose a topic** from the dropdown or enter your own search term
        2. **Select time range** (1-30 days) to analyze recent news
        3. **Pick news sources** or leave as 'All Sources' for comprehensive coverage
        4. **Click 'Analyze News'** to fetch and analyze articles
        
        ### 📊 What You'll Get:
        
        - **Sentiment Analysis** of headlines and descriptions
        - **Interactive Charts** showing trends over time
        - **Source Breakdown** to see which outlets cover your topic
        """)
    pass




if __name__ == "__main__":
    main()
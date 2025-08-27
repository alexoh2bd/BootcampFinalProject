"""
AI News API Handler
Fetches AI-related news from NewsAPI and performs sentiment analysis
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import json
from dotenv import load_dotenv
from textblob import TextBlob
from typing import List, Dict, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as SIA


# Load environment variables
load_dotenv()

class AINewsAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('NEWSAPI_KEY')
        self.base_url = "https://newsapi.org/v2/everything"
        
        if not self.api_key:
            raise ValueError("NewsAPI key not found. Please set NEWSAPI_KEY in your .env file")
    
    def fetch_ai_news(self, 
                      query: str = "artificial intelligence", 
                      days: tuple[int] = (7,14), 
                      language: str = "en",
                      sources: Optional[str] = None,
                      page_size: int = 100) -> List[Dict]:
        """
        Fetch AI-related news from NewsAPI
        
        Args:
            query: Search query for news articles
            days: Number of days to look back
            language: Language code (default: "en")
            sources: Comma-separated string of news sources
            page_size: Number of articles to fetch (max 100)
            
        Returns:
            List of news articles with metadata
        """
        # Calculate date range
        today = datetime.now()
        from_date = today - timedelta(days=days[0]) # days back from today
        to_date = today - timedelta(days=days[1]) # end date (0 = today)
        
        # Ensure from_date is earlier than to_date
        if from_date > to_date:
            from_date, to_date = to_date, from_date
        
        print(from_date, to_date)
        # Prepare API parameters
        params = {
            'q': query,
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'language': language,
            'sortBy': 'publishedAt',
            'pageSize': page_size,
            'apiKey': self.api_key
        }
        
        # Add sources if specified
        if sources:
            params['sources'] = sources
        
        try:
            # Make API request
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'ok':
                return data['articles']
            else:
                print(f"API Error: {data.get('message', 'Unknown error')}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return []
    
    def analyze_sentiment(self, text: str, model: str) -> Dict:
        """
        Analyze sentiment of given text using TextBlob
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment metrics
        """
        if not text:
            return {
                'polarity': 0.0,
                'subjectivity': 0.0,
                'label': 'neutral',
                'confidence': 0.0
            }
        blob = TextBlob(text)
        subjectivity = blob.sentiment.subjectivity

        # implement Vader Analysis for polarity scores
        if model == "Vader":
            vader = SIA()
            fullpolarity = vader.polarity_scores(text)
            polarity=fullpolarity['compound']
            polarity_thresh = 0.05
        # otherwise 
        else:
            polarity = blob.sentiment.polarity
            polarity_thresh = 0.1

        # Determine sentiment label through polarity threshold
        if polarity > polarity_thresh:
            label = 'positive'
        elif polarity < -polarity_thresh:
            label = 'negative'
        else:
            label = 'neutral'
        
        
        # Calculate confidence (distance from neutral)
        confidence = abs(polarity)
        res = {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'label': label,
            'confidence': confidence
        }
        return res
    def process_news_articles(self, articles: List[Dict], model: str) -> pd.DataFrame:
        """
        Process news articles and add sentiment analysis
        
        Args:
            articles: List of news articles from API
            
        Returns:
            DataFrame with processed articles and sentiment data
        """
        processed_articles = []
        
        for article in articles:
            # Skip articles with missing essential data
            if not article.get('title') or not article.get('publishedAt'):
                continue
            
            # Analyze sentiment of title and description
            title_sentiment = self.analyze_sentiment(article['title'], model=model)
            description_sentiment = self.analyze_sentiment(article['description'], model=model)
            
            # Combine title and description sentiment (weighted toward title)
            combined_polarity = (title_sentiment['polarity'] * 0.7 + 
                               description_sentiment['polarity'] * 0.3)
            combined_subjectivity = (title_sentiment['subjectivity'] * 0.7 + 
                                   description_sentiment['subjectivity'] * 0.3)
            # Determine overall sentiment
            if combined_polarity > 0.1:
                overall_sentiment = 'positive'
            elif combined_polarity < -0.1:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            processed_article = {
                'title': article['title'],
                'description': article.get('description', ''),
                'url': article['url'],
                'source': article['source']['name'],
                'published_at': article['publishedAt'],
                'author': article.get('author', 'Unknown'),
                'sentiment_label': overall_sentiment,
                'sentiment_polarity': combined_polarity,
                'sentiment_subjectivity': combined_subjectivity,
                'title_sentiment': title_sentiment['label'],
                'title_polarity': title_sentiment['polarity'],
                'description_sentiment': description_sentiment['label'],
                'description_polarity': description_sentiment['polarity']
            }
            
            processed_articles.append(processed_article)
        
        # Convert to DataFrame
        df = pd.DataFrame(processed_articles)
        
        # Convert published_at to datetime
        if not df.empty:
            df['published_at'] = pd.to_datetime(df['published_at'])
            df = df.sort_values('published_at', ascending=False)
        
        return df
    
    def get_ai_news_with_sentiment(self, 
                                   query: str = "artificial intelligence",
                                   days: tuple[int] = (7,14),
                                   sources: Optional[str] = None,
                                   model: str = "Textblob") -> pd.DataFrame:
        """
        Complete pipeline: fetch news and analyze sentiment
        
        Args:
            query: Search query for news articles
            days: Number of days to look back
            sources: Comma-separated string of news sources
            
        Returns:
            DataFrame with news articles and sentiment analysis
        """
        print(f"Fetching {query} news from the last {days} days...")
        
        # Fetch articles
        articles = self.fetch_ai_news(query=query, days=days, sources=sources)
        
        if not articles:
            print("No articles found.")
            return pd.DataFrame()
        
        print(f"Found {len(articles)} articles. Analyzing sentiment...")
        
        # Process and analyze
        df = self.process_news_articles(articles, model=model)
        
        print(f"Processed {len(df)} articles with sentiment analysis. \nUsed {model} for polarity analysis and Textblob for sentiment analysis.")
        return df
def load_config():
    """Load configuration from config.json"""
    with open('config.json', 'r') as f:
        return json.load(f)

if __name__ == "__main__":
    # Test the API when run directly
    analyzer = AINewsAnalyzer()
    config = load_config()
    
    print("Testing AI News Sentiment Analyzer...")
    print("=" * 50)
    
    # Test sentiment analysis
    test_texts = config["test_texts"]
    
    print("\nSentiment Analysis Examples:")
    for text in test_texts:
        sentiment = analyzer.analyze_sentiment(text)
        print(f"Text: {text}")
        print(f"Sentiment: {sentiment['label']} (polarity: {sentiment['polarity']:.2f}\n")
    
    # Test news fetching
    print("Fetching recent AI news...")
    df = analyzer.get_ai_news_with_sentiment(days=3)
    
    if not df.empty:
        print(f"\nFound {len(df)} articles")
        print("\nSentiment Distribution:")
        print(df['sentiment_label'].value_counts())
        
        print("\nTop 3 Most Positive Headlines:")
        positive_articles = df[df['sentiment_label'] == 'positive'].nlargest(3, 'sentiment_polarity')
        for _, article in positive_articles.iterrows():
            print(f"📈 {article['title']} (Score: {article['sentiment_polarity']:.2f})")
        
        print("\nTop 3 Most Negative Headlines:")
        negative_articles = df[df['sentiment_label'] == 'negative'].nsmallest(3, 'sentiment_polarity')
        for _, article in negative_articles.iterrows():
            print(f"📉 {article['title']} (Score: {article['sentiment_polarity']:.2f})")
    else:
        print("No articles found. Check your API key and internet connection.")
#!/usr/bin/env python3
"""
CLI Demo for AI News Sentiment Analyzer
Demonstrates the functionality via command line interface
"""

import argparse
import sys
from datetime import datetime
from api_handler import AINewsAnalyzer

def print_header():
    """Print a nice header for the CLI"""
    print("🤖 AI News Sentiment Analyzer")
    print("=" * 50)
    print()

def print_sentiment_emoji(sentiment):
    """Return emoji based on sentiment"""
    emoji_map = {
        'positive': '😊',
        'negative': '😞',
        'neutral': '😐'
    }
    return emoji_map.get(sentiment, '🤷')

def display_articles(df, max_articles=10):
    """Display articles in a formatted way"""
    if df.empty:
        print("❌ No articles found.")
        return
    
    print(f"📰 Found {len(df)} articles")
    print("\nSentiment Distribution:")
    sentiment_counts = df['sentiment_label'].value_counts()
    for sentiment, count in sentiment_counts.items():
        emoji = print_sentiment_emoji(sentiment)
        percentage = (count / len(df)) * 100
        print(f"  {emoji} {sentiment.title()}: {count} articles ({percentage:.1f}%)")
    
    print(f"\n📄 Top {min(max_articles, len(df))} Articles:")
    print("-" * 80)
    
    for idx, (_, article) in enumerate(df.head(max_articles).iterrows(), 1):
        sentiment_emoji = print_sentiment_emoji(article['sentiment_label'])
        score = article['sentiment_polarity']
        published = article['published_at'].strftime('%Y-%m-%d %H:%M')
        
        print(f"{idx:2}. {sentiment_emoji} [{article['source']}] {published}")
        print(f"    {article['title']}")
        print(f"    Sentiment: {article['sentiment_label'].title()} (Score: {score:.2f})")
        if article['description'] and len(article['description']) > 100:
            description = article['description'][:100] + "..."
        else:
            description = article['description'] or "No description available"
        print(f"    📝 {description}")
        print(f"    🔗 {article['url']}")
        print()

def display_sentiment_analysis(df):
    """Display detailed sentiment analysis"""
    if df.empty:
        return
    
    print("\n📊 Sentiment Analysis Summary:")
    print("-" * 40)
    
    # Overall statistics
    avg_polarity = df['sentiment_polarity'].mean()
    avg_subjectivity = df['sentiment_subjectivity'].mean()
    
    print(f"Average Polarity: {avg_polarity:.3f} (Range: -1.0 to +1.0)")
    print(f"Average Subjectivity: {avg_subjectivity:.3f} (Range: 0.0 to 1.0)")
    
    if avg_polarity > 0.1:
        overall_mood = "📈 Generally Positive"
    elif avg_polarity < -0.1:
        overall_mood = "📉 Generally Negative"
    else:
        overall_mood = "➡️ Generally Neutral"
    
    print(f"Overall Mood: {overall_mood}")
    
    # Most positive and negative articles
    if len(df[df['sentiment_label'] == 'positive']) > 0:
        most_positive = df.loc[df['sentiment_polarity'].idxmax()]
        print(f"\n😊 Most Positive: \"{most_positive['title']}\" ({most_positive['sentiment_polarity']:.2f})")
    
    if len(df[df['sentiment_label'] == 'negative']) > 0:
        most_negative = df.loc[df['sentiment_polarity'].idxmin()]
        print(f"😞 Most Negative: \"{most_negative['title']}\" ({most_negative['sentiment_polarity']:.2f})")

def display_sources(df):
    """Display source breakdown"""
    if df.empty:
        return
    
    print("\n📺 News Sources:")
    print("-" * 30)
    source_counts = df['source'].value_counts()
    for source, count in source_counts.head(10).items():
        print(f"  📰 {source}: {count} articles")

def main():
    parser = argparse.ArgumentParser(description='AI News Sentiment Analyzer CLI Demo')
    parser.add_argument('--query', '-q', 
                       default='artificial intelligence',
                       help='Search query for news articles (default: "artificial intelligence")')
    parser.add_argument('--days', '-d', 
                       type=int, 
                       default=7,
                       help='Number of days to look back (default: 7)')
    parser.add_argument('--sources', '-s',
                       help='Comma-separated list of news sources (e.g., "techcrunch,wired")')
    parser.add_argument('--max-articles', '-m',
                       type=int,
                       default=10,
                       help='Maximum number of articles to display (default: 10)')
    parser.add_argument('--sentiment-only', 
                       action='store_true',
                       help='Show only sentiment analysis summary')
    parser.add_argument('--positive-only',
                       action='store_true', 
                       help='Show only positive articles')
    parser.add_argument('--negative-only',
                       action='store_true',
                       help='Show only negative articles')
    
    args = parser.parse_args()
    
    print_header()
    
    try:
        # Initialize analyzer
        analyzer = AINewsAnalyzer()
        
        print(f"🔍 Searching for: \"{args.query}\"")
        print(f"📅 Looking back: {args.days} days")
        if args.sources:
            print(f"📰 Sources: {args.sources}")
        print()
        
        # Fetch and analyze news
        df = analyzer.get_ai_news_with_sentiment(
            query=args.query,
            days=args.days,
            sources=args.sources
        )
        
        if df.empty:
            print("❌ No articles found. Try adjusting your search parameters.")
            return
        
        # Filter by sentiment if requested
        if args.positive_only:
            df = df[df['sentiment_label'] == 'positive']
            print("🔽 Filtered to show only POSITIVE articles")
        elif args.negative_only:
            df = df[df['sentiment_label'] == 'negative']
            print("🔽 Filtered to show only NEGATIVE articles")
        
        # Display results based on options
        if args.sentiment_only:
            display_sentiment_analysis(df)
        else:
            display_articles(df, args.max_articles)
            display_sentiment_analysis(df)
            display_sources(df)
        
        print(f"\n✅ Analysis complete! Processed {len(df)} articles.")
        
    except KeyboardInterrupt:
        print("\n👋 Analysis interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print("Please check your API key and internet connection.")
        sys.exit(1)

if __name__ == "__main__":
    main()
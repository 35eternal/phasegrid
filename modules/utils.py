def chunk_dataframe(df, chunk_size=100):
    """Split dataframe into chunks for batch processing"""
    for start in range(0, len(df), chunk_size):
        yield df.iloc[start:start + chunk_size]

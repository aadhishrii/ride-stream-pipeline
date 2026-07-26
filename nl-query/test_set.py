# test_set.py

TEST_QUESTIONS = [
    # Simple lookups (single table)
    ("simple_lookup", "show me the top 5 drivers by rating"),
    ("simple_lookup", "list all payment methods that require authentication"),
    ("simple_lookup", "what cities are in the location table"),

    # Single join
    ("single_join", "which pickup city had the most rides"),
    ("single_join", "what is the average tip amount by payment method"),
    ("single_join", "how many rides were paid by card"),
    ("single_join", "which driver has the highest average rating across their rides"),

    # Multi-table joins
    ("multi_join", "what is the total fare collected per vehicle type"),
    ("multi_join", "which pickup city generates the most revenue"),
    ("multi_join", "show total rides and average fare per payment method"),
    ("multi_join", "which driver has completed the most rides"),

    # Aggregations / analytics
    ("aggregation", "what is the average surge multiplier across all rides"),
    ("aggregation", "what percentage of rides used a digital wallet"),
    ("aggregation", "what is the average distance in miles per ride"),
    ("aggregation", "what is the highest total fare recorded for a single ride"),

    # Ambiguous / edge cases
    ("edge_case", "show me rides from yesterday"),  # no clean date filter without knowing "today"
    ("edge_case", "which region had the most cancellations"),  # cancellation_reason_id exists but not resolved to text

    # Deliberately out-of-scope (should trigger ERROR: path)
    ("out_of_scope", "what is the weather in each pickup city"),
    ("out_of_scope", "predict next month's ride demand"),
    ("out_of_scope", "delete all rides with zero fare"),  # should be rejected by validation, not even reach LLM error path meaningfully — good test of is_safe_select
]
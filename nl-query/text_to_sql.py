import anthropic
from dotenv import load_dotenv
load_dotenv()
client = anthropic.Anthropic()  # picks up ANTHROPIC_API_KEY from env automatically

SCHEMA_CONTEXT = """
Tables:
uber.bronze.dim_passenger(passenger_id, passenger_name, passenger_email, passenger_phone)
uber.bronze.dim_driver(driver_id, driver_name, driver_rating, driver_phone, driver_license)
uber.bronze.dim_vehicle(vehicle_id, vehicle_make_id, vehicle_type_id, vehicle_model, vehicle_color, license_plate, vehicle_make, vehicle_type)
uber.bronze.dim_payment(payment_method_id, payment_method, is_card, requires_auth)
uber.bronze.dim_booking(ride_id, confirmation_number, dropoff_location_id, ride_status_id, dropoff_city_id, cancellation_reason_id, dropoff_address, dropoff_latitude, dropoff_longitude, booking_timestamp, dropoff_timestamp, pickup_address, pickup_latitude, pickup_longitude, pickup_location_id)
uber.bronze.dim_location(pickup_city_id, pickup_city, city_updated_at, region, state)
uber.bronze.fact(ride_id, pickup_city_id, payment_method_id, driver_id, passenger_id, vehicle_id, distance_miles, duration_minutes, base_fare, distance_fare, time_fare, surge_multiplier, total_fare, tip_amount, rating, base_rate, per_mile, per_minute)

Notes:
- Always use fully-qualified table names in the form uber.bronze.<table>
- dim_location uses SCD Type 2 (tracked via city_updated_at) — all other dimensions are SCD Type 1
- fact joins to dim_driver, dim_passenger, dim_vehicle, dim_payment, dim_location on their respective id columns
- fact joins to dim_booking on ride_id for timestamps and address details
- booking_timestamp and dropoff_timestamp live in dim_booking, not fact
"""

def generate_sql(question: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=f"""You convert natural language questions into a single Databricks SQL SELECT query.
Schema:
{SCHEMA_CONTEXT}

Rules:
- Output ONLY the SQL query, no explanation, no markdown fences
- Only generate SELECT statements
- If the question can't be answered with this schema, output: ERROR: <reason>""",
        messages=[{"role": "user", "content": question}]
    )
    return response.content[0].text.strip()



if __name__ == "__main__":
    test_questions = [
        "which pickup city had the most rides",
        "what is the average tip amount by payment method",
        "show me the top 5 drivers by rating",
        "how many rides were paid by card"
    ]
    for q in test_questions:
        print(f"Q: {q}")
        print(f"SQL: {generate_sql(q)}\n")
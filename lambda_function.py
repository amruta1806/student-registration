import json
import os
import uuid
from datetime import datetime, timezone

import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("TABLE_NAME", "registrations"))

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}

REQUIRED_FIELDS = ["name", "email", "phone", "course"]


def response(status, body):
    return {"statusCode": status, "headers": HEADERS, "body": json.dumps(body)}


def lambda_handler(event, context):
    # Browser preflight request (CORS)
    method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
    )
    if method == "OPTIONS":
        return response(200, {"message": "OK"})

    # Read the form data (API Gateway sends it as a JSON string in "body")
    try:
        data = event.get("body", event)
        if isinstance(data, str):
            data = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return response(400, {"error": "Invalid JSON"})

    # Validate required fields
    missing = [f for f in REQUIRED_FIELDS if not str(data.get(f, "")).strip()]
    if missing:
        return response(400, {"error": "Missing fields: " + ", ".join(missing)})

    item = {
        "registrationId": str(uuid.uuid4()),
        "name": data["name"].strip(),
        "email": data["email"].strip().lower(),
        "phone": data["phone"].strip(),
        "course": data["course"].strip(),
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    try:
        table.put_item(Item=item)
    except Exception as e:
        print("DynamoDB error:", e)
        return response(500, {"error": "Could not save registration"})

    return response(
        200,
        {"message": "Registration saved", "registrationId": item["registrationId"]},
    )
import json
import boto3
from boto3.dynamodb.conditions import Key
import os

dynamodb = boto3.resource("dynamodb")
CHAT_MESSAGES_TABLE = os.environ.get("CHAT_MESSAGES_TABLE", "ChatMessages")
chat_messages = dynamodb.Table(CHAT_MESSAGES_TABLE)

def lambda_handler(event, context):
    try:
        # ---------- 1️⃣ Get Cognito user ----------
        claims = (
            event.get("requestContext", {})
                 .get("authorizer", {})
                 .get("jwt", {})
                 .get("claims", {})
        )
        user_id = claims.get("sub") if claims else None
        if not user_id:
            return {
                "statusCode": 401,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Unauthorized - missing Cognito claims"})
            }

        # ---------- 2️⃣ Get sessionId ----------
        params = event.get("queryStringParameters") or {}
        session_id = params.get("sessionId")
        if not session_id:
            return {
                "statusCode": 400,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "sessionId is required"})
            }

        # ---------- 3️⃣ Query DynamoDB ----------
        try:
            response = chat_messages.query(
                KeyConditionExpression=Key('sessionId').eq(session_id),
                ScanIndexForward=True  # oldest first
            )
            messages = response.get("Items", [])
        except Exception as e:
            print("DynamoDB query error:", e)
            return {
                "statusCode": 500,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"error": "Failed to query messages"})
            }

        # ---------- 4️⃣ Format ----------
        formatted = [{"role": m["role"], "message": m["content"]} for m in messages]

        return {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(formatted)
        }

    except Exception as e:
        print("Unexpected error:", e)
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)})
        }

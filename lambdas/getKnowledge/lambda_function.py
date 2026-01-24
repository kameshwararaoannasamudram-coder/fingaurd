import json
import boto3
import os
import time

bedrock = boto3.client("bedrock-agent-runtime")
dynamodb = boto3.resource("dynamodb")

KNOWLEDGE_BASE_ID = os.environ["KNOWLEDGE_BASE_ID"]
MODEL_ARN = os.environ["MODEL_ARN"]

CHAT_MESSAGES_TABLE = os.environ.get("CHAT_MESSAGES_TABLE", "ChatMessages")
CHAT_SESSIONS_TABLE = os.environ.get("CHAT_SESSIONS_TABLE", "ChatSessions")

chat_messages = dynamodb.Table(CHAT_MESSAGES_TABLE)
chat_sessions = dynamodb.Table(CHAT_SESSIONS_TABLE)


def lambda_handler(event, context):
    try:
        # ---------- 1️⃣ User ----------
        claims = (
            event.get("requestContext", {})
                 .get("authorizer", {})
                 .get("jwt", {})
                 .get("claims", {})
        )
        user_id = claims.get("sub", "TEST_USER")

        # ---------- 2️⃣ Body ----------
        body = json.loads(event.get("body", "{}"))
        prompt = body.get("prompt")
        session_id = body.get("sessionId")
        is_first = body.get("isFirstMessage", False)

        if not prompt or not session_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "prompt and sessionId required"})
            }

        now = int(time.time() * 1000)

        # ---------- 3️⃣ Create session (once) ----------
        if is_first:
            chat_sessions.put_item(
                Item={
                    "userId": user_id,
                    "sessionId": session_id,
                    "title": prompt[:60],
                    "createdAt": now
                },
                ConditionExpression="attribute_not_exists(sessionId)"
            )

        # ---------- 4️⃣ Save user message ----------
        chat_messages.put_item(
            Item={
                "sessionId": session_id,
                "timestamp": now,
                "role": "user",
                "content": prompt
            }
        )

        # ---------- 5️⃣ Bedrock ----------
        try:
            result = bedrock.retrieve_and_generate(
                input={"text": prompt},
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                        "modelArn": MODEL_ARN
                    }
                }
            )
            answer = result["output"]["text"]
        except Exception as e:
            print("Bedrock error:", e)
            answer = "⚠️ Bedrock failed to respond"

        # ---------- 6️⃣ Save assistant ----------
        chat_messages.put_item(
            Item={
                "sessionId": session_id,
                "timestamp": now + 1,
                "role": "assistant",
                "content": answer
            }
        )

        return {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"response": answer})
        }

    except Exception as e:
        print("ERROR:", e)
        return {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": str(e)})
        }

import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { QueryCommand } from "@aws-sdk/lib-dynamodb";

const db = new DynamoDBClient({});

export const handler = async (event) => {
  console.log("EVENT:", JSON.stringify(event));

  const userId = event.requestContext.authorizer.jwt.claims.sub;

  const result = await db.send(
    new QueryCommand({
      TableName: "ChatSessions",
      KeyConditionExpression: "userId = :u",
      ExpressionAttributeValues: {
        ":u": userId
      }
    })
  );

  return {
    statusCode: 200,
    headers: {
      "Access-Control-Allow-Origin": "*"
    },
    body: JSON.stringify(result.Items || [])
  };
};

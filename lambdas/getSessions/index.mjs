export const handler = async (event) => {
  // TODO implement
  const response = {
    statusCode: 200,
    body: JSON.stringify('Hello from Lambda!'),
    Headers: process.env.SESSIONS_TABLE

  };
  return response;
};
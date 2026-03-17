# Simple health check endpoint to verify Vercel Python runtime works

def handler(request):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": '{"status": "ok", "message": "Vercel Python runtime works!"}'
    }

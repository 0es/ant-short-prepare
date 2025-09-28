from flask import Flask, request, jsonify
import json

app = Flask(__name__)


@app.route("/callback", methods=["POST"])
def callback():
    """
    HTTP callback endpoint that prints the request body
    """
    try:
        # Get the request body
        body = request.get_data(as_text=True)

        # Print the raw body
        print("=== Callback Request Body ===")
        print(body)
        print("=" * 30)

        # Try to parse as JSON if possible
        try:
            json_data = request.get_json()
            if json_data:
                print("=== Parsed JSON Data ===")
                print(json.dumps(json_data, indent=2, ensure_ascii=False))
                print("=" * 24)
        except Exception as e:
            print(f"Body is not valid JSON: {e}")

        # Print headers for additional context
        print("=== Request Headers ===")
        for header, value in request.headers:
            print(f"{header}: {value}")
        print("=" * 23)

        # Return success response
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Callback received and logged",
                    "body_length": len(body),
                }
            ),
            200,
        )

    except Exception as e:
        print(f"Error processing callback: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """
    Health check endpoint
    """
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    print("Starting HTTP Callback Service...")
    print("Callback endpoint: POST /callback")
    print("Health check: GET /health")
    print("Server running on http://0.0.0.0:5000")

    app.run(host="0.0.0.0", port=5000, debug=True)

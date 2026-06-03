# Notion first sends a verification code. This block of code is to capture it in the server Log so we can save it

# --- Modules ---
from flask import Flask, request, jsonify

# --- Initial Setup ---
app = Flask(__name__)

# --- Main Webhook ---
@app.route('/api/v1/doc/forge', methods=['POST'])
def forge_doc():
    data = request.get_json()
    print("Incoming payload:", data)  # this shows up in Render logs
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    print("Starting local server on port 5000...")
    app.run(port=5000)
from flask import Flask, request, jsonify
import time
import random

app = Flask(__name__)

@app.route('/api/process', methods=['POST'])
def dummy_process():
    """Dummy API for testing Monitor Bot"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        # Simulate processing time
        time.sleep(random.uniform(1, 3))
        
        # Random responses for testing
        responses = [
            {"status": "success", "message": "Link processed successfully", "posted": True},
            {"status": "duplicate", "message": "Link already processed", "posted": False},
            {"status": "error", "message": "Processing failed", "posted": False}
        ]
        
        # 80% success, 10% duplicate, 10% error
        weights = [0.8, 0.1, 0.1]
        response = random.choices(responses, weights=weights)[0]
        
        print(f"📡 Dummy API processed: {url} → {response['status']}")
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "message": "Dummy Token Bot API"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

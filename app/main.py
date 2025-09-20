from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Hello Chief! Your Flask API is live 🚀"
    })

@app.route("/echo", methods=["POST"])
def echo():
    data = request.json
    return jsonify({
        "you_sent": data,
        "status": "success"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

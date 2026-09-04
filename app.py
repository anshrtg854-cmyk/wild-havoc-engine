from flask import Flask, request, jsonify
from flask_cors import CORS
from game_engine import WildHavocGameEngine

app = Flask(__name__)
CORS(app)

engine = WildHavocGameEngine()

@app.route('/api/spin', methods=['POST'])
def spin():
    data = request.json or {}
    cost_mult = data.get('cost_multiplier', 1.0)
    special_mode = data.get('special_mode', None)
    active_feature = data.get('active_feature', None)
    
    result = engine.start_spin(
        cost_multiplier=cost_mult,
        special_mode=special_mode,
        active_feature_mode=active_feature
    )
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

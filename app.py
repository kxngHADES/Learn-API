from flask import Flask, jsonify, request
from supabase import create_client, Client
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Supabase init
supabase_url = "https://hyadyjyzochlbndzlgij.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh5YWR5anl6b2NobGJuZHpsZ2lqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MjcyOTg1MywiZXhwIjoyMDU4MzA1ODUzfQ.DC0_3-As0uq6cyHX5LX30-BFpTxAszjpYlSy0BBz4Tg"
supabase: Client = create_client(supabase_url, supabase_key)


def verify_jwt(supabase: Client):
    def decorator(func):
        def wrapper(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({"error": "Authorization token is missing!"}), 401

            try:
                user = supabase.auth.get_user(token)
                request.user = user
                return func(*args, **kwargs)
            except Exception as e:
                return jsonify({"error": "Invalid or expired token!", "details": str(e)}), 401
        return wrapper
    return decorator

@app.route('/')
def home():
    return {
        "message": "Welcome to the Solo Leveling API!"
    }

@app.route('/hunter')
def hunter():
    sung = [
        {
            "name": "Sung Jin-Woo",
            "rank": "S-Rank"
        }
    ]
    return jsonify(sung)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/hunters', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
@verify_jwt(supabase)
def hunters():
    page = int(request.args.get('page', 1))  # Default to page 1
    per_page = int(request.args.get('per_page', 10))  # Default to 10 items per page

    start = (page - 1) * per_page
    end = start + per_page - 1
    rank = request.args.get('rank')
    name = request.args.get('name')

    query = supabase.table('hunters').select('name','rank').range(start, end)

    if rank:
        query = query.eq('rank', rank)  # Filter by rank
    if name:
        query = query.ilike('name', f'%{name}%')  # Case-insensitive search by name

    response = query.execute()
    return jsonify(response.data), 200

@app.route('/hunters/<name>', methods=['PUT'])
def update_hunter(name):
    new_data = request.get_json()
    if not new_data.get('rank'):
        return jsonify({"error": "Rank is required!"}), 400

    response = supabase.table('hunters').update(new_data).eq('name', name).execute()
    if not response.data:
        return jsonify({"error": "Hunter not found!"}), 404
    return jsonify(response.data[0]), 200

@app.route('/hunters/<name>', methods=['DELETE'])
def delete_hunters(name):
    response = supabase.table('hunters').delete().eq('name', name).execute()
    if not response.data:
        return jsonify({"error": "Hunter not found!"}), 404
    return jsonify({"message": "Hunter banished!"}), 200

@app.route('/register', methods=['POST'])
def register():
    user_data = request.get_json()
    email = user_data.get('email')
    password = user_data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required!"}), 400

    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        user_info = {
            "id": response.user.id,
            "email": response.user.email,
            "created_at": response.user.created_at
        }

        return jsonify({"message": "User registered!", "user": user_info}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    user_data = request.get_json()
    email = user_data.get('email')
    password = user_data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required!"}), 400

    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        user_info = {
            "id": response.user.id,
            "email": response.user.email,
            "created_at": response.user.created_at
        }

        return jsonify({
            "message": "Login successful!",
            "user": user_info,
            "token": response.session.access_token  # 🌟 JWT token included
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 401

if __name__ == '__main__':
    app.run(debug=True)
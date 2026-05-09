import os
from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
from dotenv import load_dotenv
import database

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='static')
app.secret_key = os.urandom(24) # Needed for session management

# Initialize database
database.init_db()

# Configure Gemini API
# It's important to gracefully handle missing API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY and GEMINI_API_KEY != "your_api_key_here":
    genai.configure(api_key=GEMINI_API_KEY)
    # Using a free-tier available model
    model = genai.GenerativeModel('gemini-flash-latest')
else:
    model = None
    print("WARNING: Gemini API key not found. Chat feature will not work.")

# System prompt to define the persona
SYSTEM_PROMPT = """
You are FitAI, a friendly, motivating, and highly knowledgeable AI Personal Fitness Coach. 
Your goal is to help users achieve their fitness goals (weight loss, muscle gain, maintenance, etc.).
You communicate in a simple, easy-to-understand, and encouraging manner.
When suggesting diets, strongly prefer Indian diets unless the user specifies otherwise. 
Provide clear, actionable advice, workout plans, and meal suggestions.
Format your responses using Markdown for readability (use bolding, bullet points, and short paragraphs).
Always consider the user's age, gender, height, weight, activity level, and goals if they have provided them.
Do not sound robotic. Be energetic and supportive!
"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    if not model:
        return jsonify({"error": "Gemini API key is not configured on the server. Please check the .env file."}), 500

    data = request.json
    user_message = data.get('message')
    
    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    # Initialize chat history in session if it doesn't exist
    if 'chat_history' not in session:
        session['chat_history'] = [
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "model", "parts": ["Understood. I am FitAI, your friendly personal fitness coach. Let's get started!"]}
        ]

    try:
        # Append user message to history
        session['chat_history'].append({"role": "user", "parts": [user_message]})
        
        # Start a chat session with the accumulated history
        chat_session = model.start_chat(history=session['chat_history'][:-1]) # Pass all but the very last message as history
        
        # Send the latest message
        response = chat_session.send_message(user_message)
        
        # Append bot response to history
        session['chat_history'].append({"role": "model", "parts": [response.text]})
        
        # Keep history from growing too large (e.g., keep last 20 messages + system prompt)
        if len(session['chat_history']) > 22:
            session['chat_history'] = session['chat_history'][:2] + session['chat_history'][-20:]
            
        session.modified = True # Ensure session is saved

        return jsonify({"response": response.text})
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({"error": f"Failed to get response from AI: {str(e)}"}), 500

@app.route('/api/clear_chat', methods=['POST'])
def clear_chat():
    if 'chat_history' in session:
        session.pop('chat_history')
    return jsonify({"success": True})

@app.route('/api/bmi', methods=['POST'])
def calculate_bmi():
    data = request.json
    try:
        height_cm = float(data.get('height'))
        weight_kg = float(data.get('weight'))
        
        if height_cm <= 0 or weight_kg <= 0:
            return jsonify({"error": "Height and weight must be positive numbers"}), 400
            
        height_m = height_cm / 100
        bmi = weight_kg / (height_m * height_m)
        bmi = round(bmi, 1)
        
        category = ""
        if bmi < 18.5:
            category = "Underweight"
        elif 18.5 <= bmi < 24.9:
            category = "Normal weight"
        elif 25 <= bmi < 29.9:
            category = "Overweight"
        else:
            category = "Obese"
            
        return jsonify({
            "bmi": bmi,
            "category": category
        })
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid input for height or weight"}), 400

@app.route('/api/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        data = request.json
        database.save_profile(data)
        
        # Inject profile context into chat history
        if 'chat_history' in session:
            context_msg = f"My profile updated: Age: {data.get('age')}, Gender: {data.get('gender')}, Height: {data.get('height')}cm, Weight: {data.get('weight')}kg, Goal: {data.get('goal')}, Activity Level: {data.get('activity_level')}."
            session['chat_history'].append({"role": "user", "parts": [context_msg]})
            session['chat_history'].append({"role": "model", "parts": ["Got it! I've updated your profile and will keep this in mind for future recommendations."]})
            session.modified = True
            
        return jsonify({"success": True, "message": "Profile saved successfully"})
    else:
        profile_data = database.get_profile()
        return jsonify(profile_data if profile_data else {})

@app.route('/api/progress', methods=['GET', 'POST'])
def progress():
    if request.method == 'POST':
        data = request.json
        date = data.get('date')
        weight = data.get('weight')
        notes = data.get('notes', '')
        
        if not date or not weight:
            return jsonify({"error": "Date and weight are required"}), 400
            
        database.log_progress(date, weight, notes)
        return jsonify({"success": True})
    else:
        progress_data = database.get_progress()
        return jsonify(progress_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

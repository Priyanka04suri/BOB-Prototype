import datetime
import logging
from datetime import datetime
import re

import google.generativeai as genai
from flask import jsonify, request
from flask_cors import CORS

import gemini_call
import sql
import stock as stk
from application import app
from config import Config

CORS(app)

# Initialize Gemini API
genai.configure(api_key=Config.GEMINI_API_KEY)

context_data = 'You are a friendly financial chatbot named Monetize.ai. The user will ask you questions, and you will provide polite responses.\n\n'

# Create a message list to pass into Gemini
messages = []

def record(message):
    """
    Record messages into a global variable

    Args:
        message (string): message content
    """
    global messages
    messages.append(message)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        global messages
        email = request.cookies.get('email')

        data = request.get_json()
        user_message = data['prompt']
        print("user message received:")
        print(user_message + '\n')

        # decide which action to use based on user message input
        with open('prompt.txt', 'r') as prompt:
            prompt_input = prompt.read()
            result = gemini_call.gemini(prompt_input + user_message + "\nOutput: |")
            
            output_list = result.split(' ')
            case = output_list[0]
            print("case:", case)
            output_data = output_list[1:]
            print("output data: ", output_data)


        # Rest of the function remains largely the same, just replace open_ai_call.gpt_3 and open_ai_call.gpt_with_info with gemini_call.gemini

        # For example:
        result = gemini_call.gemini_with_info([context_data + ' '.join(messages) + ' ' + user_message])
        record(result)

        # add user message to database
        sql.add_message(email, user_message, datetime.now(), False)

        # add bot response to database
        sql.add_message(email, result, datetime.now(), True)

        return jsonify({'response': result})

    except Exception as e:
        return jsonify({'response': f'Sorry, an error occurred: {str(e)}'})

# Other routes remain the same

@app.route('/update_gemini_key', methods=['POST'])
def update_gemini_key():
    """
    Update Gemini key

    Args:
        key (string): new Gemini key
    """
    data = request.get_json()

    print(data)

    email = request.cookies.get('email')
    key = data['key']
    print("user key received:")
    print(key + '\n')

    print("updating key\n")
    update_success = gemini_call.update_gemini_key(email, key)
    
    if update_success:
        print("key updated\n")
        return jsonify({'response': 'success'})
    else:
        return jsonify({'response': 'error'})

@app.route('/update_field', methods=['POST'])
def update_field():
    email = request.cookies.get('email')
    data = request.get_json()
    print(data)
    field = data['field']
    new_value = data['newValue']

    try:
        if field == 'name':
            sql.update_name(email, new_value)
        elif field == 'email':
            sql.update_email(email, new_value)
        elif field == 'phone':
            sql.update_phone(email, new_value)
        elif field == 'gemini-key':
            gemini_call.update_gemini_key(email, new_value)
    
    except ValueError as error:
        print("Error: ", error)
        return jsonify({'error': str(error)})
    except Exception as e:
        print("error in app.py:", str(e))
        return jsonify({'error': 'unknown error'})

    return jsonify({'response': 'success'})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
import time
import google.generativeai as genai
from flask import request
import sql
from config import Config

# Initialize Gemini API
genai.configure(api_key=Config.GEMINI_API_KEY)

def update_gemini_key(email, key):
    sql.update_api_key(email, key)
    Config.GEMINI_API_KEY = key
    genai.configure(api_key=key)
    
    # Test if key is valid
    try:
        gemini(["test api key"])
        return True
    except Exception as e:
        raise ValueError(f"API key not working: {str(e)}")

def gemini(message_list):
    print("Starting Gemini...\n")
    start_time = time.time()

    try:
        model = genai.GenerativeModel('gemini-pro')
        chat = model.start_chat()
        
        for message in message_list:
            response = chat.send_message(message)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"\nTime elapsed: {elapsed_time} seconds\n")

        return response.text
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
        return f"An error occurred: {str(e)}"

def gemini_with_info(message_list, temperature=1):
    """Uses Google's Gemini API to generate a response to a query, with user information and portfolio information appended to the query

    Args:
    message_list (list): List of message dictionaries to be sent to the API
    temperature (float): The temperature of the response, which controls randomness. Higher values make the response more random and vice versa.
        (default is 1)

    Returns:
        response: The response from the API
    """

    email = request.cookies.get('email')
    user_data = sql.get_user_data(email)[1]
    user_info = "User information: Username: " + user_data[0] + ", Email: " + user_data[1] + ", Phone number: " + str(user_data[2]) + "."

    portfolio_data = sql.get_stock_data(email)[1]
    portfolio_info = f"User's risk tolerance: {user_data[3]}. "
    if portfolio_data == []:
        portfolio_info += "User's portfolio is empty."
    else:
        portfolio_info += "User's portfolio information:"
        for stock in portfolio_data:
            portfolio_info += " Date added: " + stock[0] + ", Ticker: " + stock[1] + ", Quantity: " + str(stock[2]) + ", Start price: " + str(stock[3]) + ", End price: " + str(stock[4]) + ", Return percent: " + str(stock[5]) + ", Return amount: " + str(stock[6]) + ", Total: " + str(stock[7]) + "."

    system_message = {"You are a friendly financial chatbot named Monetize.ai. The user will ask you questions, and you will provide polite responses. " + user_info + ' ' + portfolio_info + ". If user ask to change risk tolerance, response that risk tolerance has been changed. If user bought or sold a stock, response that their portfolio has been updated and answer detail about their profit."}
    
    if isinstance(message_list, str):
        message_list = [message_list]
    elif not isinstance(message_list, list):
        message_list = []

    message_list.insert(0, system_message)

    response = gemini(message_list)
    return response
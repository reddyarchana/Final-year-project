from flask import Flask, url_for, redirect, render_template, request
import mysql.connector, os, re
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import joblib
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import torch.nn.functional as F


app = Flask(__name__)
app.secret_key = 'admin'

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    port="3306",
    database='stressdetection'
)

mycursor = mydb.cursor()

def executionquery(query,values):
    mycursor.execute(query,values)
    mydb.commit()
    return

def retrivequery1(query,values):
    mycursor.execute(query,values)
    data = mycursor.fetchall()
    return data

def retrivequery2(query):
    mycursor.execute(query)
    data = mycursor.fetchall()
    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        c_password = request.form['c_password']
        if password == c_password:
            query = "SELECT UPPER(email) FROM users"
            email_data = retrivequery2(query)
            email_data_list = []
            for i in email_data:
                email_data_list.append(i[0])
            if email.upper() not in email_data_list:
                query = "INSERT INTO users (email, password) VALUES (%s, %s)"
                values = (email, password)
                executionquery(query, values)
                return render_template('login.html', message="Successfully Registered!")
            return render_template('register.html', message="This email ID is already exists!")
        return render_template('register.html', message="Conform password is not match!")
    return render_template('register.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        query = "SELECT UPPER(email) FROM users"
        email_data = retrivequery2(query)
        email_data_list = []
        for i in email_data:
            email_data_list.append(i[0])

        if email.upper() in email_data_list:
            query = "SELECT UPPER(password) FROM users WHERE email = %s"
            values = (email,)
            password__data = retrivequery1(query, values)
            if password.upper() == password__data[0][0]:
                global user_email
                user_email = email

                return render_template('home.html')
            return render_template('login.html', message= "Invalid Password!!")
        return render_template('login.html', message= "This email ID does not exist!")
    return render_template('login.html')


@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')




# Load the pretrained BERT model and tokenizer (replace with your model path)
model = BertForSequenceClassification.from_pretrained(r'mental_health_model\bert_mental_health_model')  
tokenizer = BertTokenizer.from_pretrained(r'mental_health_model\bert_tokenizer')  

# Ensure the model is in evaluation mode
model.eval()

# Define label encoding mapping
label_mapping = {
    0: 'Anxiety',
    1: 'Bipolar',
    2: 'Depression',
    3: 'Normal',
    4: 'Personality disorder',
    5: 'Stress',
    6: 'Suicidal'
}

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    prediction = None
    
    if request.method == 'POST':
        # Get the text input from the form
        text_input = request.form['text_input']
        
        # Tokenize the input text
        inputs = tokenizer(text_input, return_tensors="pt", truncation=True, padding=True, max_length=512)
        
        # Perform inference
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Get prediction
        logits = outputs.logits
        predicted_class_id = torch.argmax(logits, dim=1).item()
        
        # Map the predicted class id to a label using the label mapping
        prediction = label_mapping.get(predicted_class_id, 'Unknown')  # Default to 'Unknown' if prediction is out of bounds
            
    # Render the prediction page with the result
    return render_template('prediction.html', prediction=prediction)



suicide_model = BertForSequenceClassification.from_pretrained(r'suicide_model\bert_suicide_model')  
suicide_tokenizer = BertTokenizer.from_pretrained(r'suicide_model\bert_tokenizer') 

# Ensure the model is in evaluation mode
suicide_model.eval()

# Define label encoding mapping for suicide classification (0: Non-Suicidal, 1: Suicidal)
suicide_label_mapping = {
    0: 'Non-Suicidal',
    1: 'Suicidal'
}

@app.route('/result', methods=['GET', 'POST'])
def result():
    prediction = None
    
    if request.method == 'POST':
        # Get the text input from the form
        text_input = request.form['text_input']
        
        # Tokenize the input text for suicide prediction
        inputs = suicide_tokenizer(text_input, return_tensors="pt", truncation=True, padding=True, max_length=512)
        
        # Perform inference
        with torch.no_grad():
            outputs = suicide_model(**inputs)
        
        # Get prediction (logits are returned, we need to get the class with the highest logit)
        logits = outputs.logits
        predicted_class_id = torch.argmax(logits, dim=1).item()
        
        # Map the predicted class id to a label using the label mapping
        prediction = suicide_label_mapping.get(predicted_class_id, 'Unknown')  # Default to 'Unknown' if prediction is out of bounds

    # Render the prediction page with the result
    return render_template('result.html', prediction=prediction)


if __name__ == '__main__':
    app.run(debug = True)
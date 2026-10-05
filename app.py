import os
import threading

import streamlit as st
import requests

from dotenv import load_dotenv

from fastapi import FastAPI
from pydantic import BaseModel

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime
)

from sqlalchemy.orm import declarative_base, sessionmaker

from datetime import datetime

import uvicorn


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000"
)


# =========================================================
# DATABASE
# =========================================================

DATABASE_URL = "sqlite:///./customer_support.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# =========================================================
# DATABASE MODELS
# =========================================================

class Customer(Base):

    __tablename__ = "customers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False
    )


class Chat(Base):

    __tablename__ = "chats"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    customer_name = Column(
        String(100),
        nullable=False
    )

    question = Column(
        Text,
        nullable=False
    )

    answer = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


Base.metadata.create_all(
    bind=engine
)


# =========================================================
# PYDANTIC MODELS
# =========================================================

class ChatRequest(BaseModel):

    customer_name: str

    question: str


class CustomerRequest(BaseModel):

    name: str

    email: str


# =========================================================
# FASTAPI
# =========================================================

api = FastAPI(
    title="AI Customer Support API",
    version="1.0"
)


# =========================================================
# AI RESPONSE
# =========================================================

def generate_ai_response(question):

    question = question.lower()

    if "hello" in question or "hi" in question:

        return (
            "Hello! 👋 Welcome to our customer support. "
            "How can I help you today?"
        )

    elif "order" in question:

        return (
            "I can help you with your order. "
            "Please provide your order ID."
        )

    elif "refund" in question:

        return (
            "Our refund process normally takes "
            "5 to 7 business days."
        )

    elif "return" in question:

        return (
            "You can request a product return "
            "within 30 days of delivery."
        )

    elif "price" in question or "cost" in question:

        return (
            "Please provide the product name "
            "so I can help you with its price."
        )

    elif "password" in question:

        return (
            "You can reset your password using "
            "the Forgot Password option."
        )

    elif "payment" in question:

        return (
            "We support multiple secure payment "
            "methods. Please tell me your payment issue."
        )

    elif "cancel" in question:

        return (
            "I can help with cancellation. "
            "Please provide your order ID."
        )

    elif "thank" in question:

        return (
            "You're welcome! 😊 "
            "Is there anything else I can help you with?"
        )

    else:

        return (
            "Thank you for contacting customer support. "
            "I understand your question. "
            "Our support team will help you shortly."
        )


# =========================================================
# API: HOME
# =========================================================

@api.get("/")
def home():

    return {
        "message": "AI Customer Support API is running"
    }


# =========================================================
# API: CHAT
# =========================================================

@api.post("/chat")
def chat(request: ChatRequest):

    db = SessionLocal()

    answer = generate_ai_response(
        request.question
    )

    new_chat = Chat(
        customer_name=request.customer_name,
        question=request.question,
        answer=answer
    )

    db.add(new_chat)

    db.commit()

    db.close()

    return {

        "success": True,

        "question": request.question,

        "answer": answer
    }


# =========================================================
# API: ADD CUSTOMER
# =========================================================

@api.post("/customers")
def add_customer(
    request: CustomerRequest
):

    db = SessionLocal()

    existing_customer = (
        db.query(Customer)
        .filter(
            Customer.email == request.email
        )
        .first()
    )

    if existing_customer:

        db.close()

        return {
            "success": False,
            "message": "Customer already exists"
        }

    customer = Customer(
        name=request.name,
        email=request.email
    )

    db.add(customer)

    db.commit()

    db.refresh(customer)

    customer_id = customer.id

    db.close()

    return {

        "success": True,

        "message": "Customer added successfully",

        "customer_id": customer_id
    }


# =========================================================
# API: CUSTOMERS
# =========================================================

@api.get("/customers")
def get_customers():

    db = SessionLocal()

    customers = db.query(
        Customer
    ).all()

    result = [

        {
            "id": customer.id,

            "name": customer.name,

            "email": customer.email
        }

        for customer in customers

    ]

    db.close()

    return result


# =========================================================
# API: CHAT HISTORY
# =========================================================

@api.get("/chats")
def get_chats():

    db = SessionLocal()

    chats = (
        db.query(Chat)
        .order_by(
            Chat.id.desc()
        )
        .all()
    )

    result = [

        {
            "id": chat.id,

            "customer_name":
                chat.customer_name,

            "question":
                chat.question,

            "answer":
                chat.answer,

            "created_at":
                str(chat.created_at)
        }

        for chat in chats

    ]

    db.close()

    return result


# =========================================================
# API: DASHBOARD
# =========================================================

@api.get("/dashboard")
def dashboard():

    db = SessionLocal()

    total_customers = (
        db.query(Customer).count()
    )

    total_chats = (
        db.query(Chat).count()
    )

    db.close()

    return {

        "total_customers":
            total_customers,

        "total_chats":
            total_chats
    }


# =========================================================
# START FASTAPI IN BACKGROUND
# =========================================================

def start_api():

    uvicorn.run(
        api,
        host="127.0.0.1",
        port=8000,
        log_level="warning"
    )


if "api_started" not in st.session_state:

    thread = threading.Thread(
        target=start_api,
        daemon=True
    )

    thread.start()

    st.session_state.api_started = True


# =========================================================
# STREAMLIT CONFIG
# =========================================================

st.set_page_config(

    page_title="AI Customer Support",

    page_icon="🤖",

    layout="wide"
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "🤖 AI Customer Support"
)

page = st.sidebar.radio(

    "Select Page",

    [
        "Customer Chat",
        "Admin Dashboard"
    ]
)


# =========================================================
# CUSTOMER CHAT
# =========================================================

if page == "Customer Chat":

    st.title(
        "🤖 AI Customer Support Chatbot"
    )

    st.write(
        "Welcome! Ask us about orders, "
        "returns, refunds, payments and accounts."
    )

    st.divider()

    customer_name = st.text_input(
        "Customer Name"
    )

    email = st.text_input(
        "Email"
    )

    question = st.text_area(

        "Your Question",

        placeholder=
        "Example: Where is my order?"
    )

    if st.button(
        "Send Message",
        type="primary"
    ):

        if not customer_name:

            st.warning(
                "Please enter your name."
            )

        elif not email:

            st.warning(
                "Please enter your email."
            )

        elif not question:

            st.warning(
                "Please enter your question."
            )

        else:

            try:

                # Add customer

                requests.post(

                    f"{API_URL}/customers",

                    json={

                        "name":
                            customer_name,

                        "email":
                            email
                    }
                )


                # Send question

                response = requests.post(

                    f"{API_URL}/chat",

                    json={

                        "customer_name":
                            customer_name,

                        "question":
                            question
                    }
                )


                if response.status_code == 200:

                    data = response.json()

                    st.success(
                        "AI Response"
                    )

                    st.info(
                        data["answer"]
                    )

                else:

                    st.error(
                        "Unable to process your question."
                    )


            except Exception as e:

                st.error(
                    f"Error: {e}"
                )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

elif page == "Admin Dashboard":

    st.title(
        "📊 Admin Dashboard"
    )

    st.write(
        "Monitor customers and customer-support conversations."
    )

    st.divider()

    try:

        # ------------------------------------------
        # DASHBOARD STATISTICS
        # ------------------------------------------

        response = requests.get(

            f"{API_URL}/dashboard"
        )

        dashboard = response.json()


        col1, col2 = st.columns(2)


        with col1:

            st.metric(

                "👥 Total Customers",

                dashboard[
                    "total_customers"
                ]
            )


        with col2:

            st.metric(

                "💬 Total Conversations",

                dashboard[
                    "total_chats"
                ]
            )


        st.divider()


        # ------------------------------------------
        # CUSTOMERS
        # ------------------------------------------

        st.subheader(
            "👥 Customers"
        )

        response = requests.get(

            f"{API_URL}/customers"
        )

        customers = response.json()


        if customers:

            st.dataframe(

                customers,

                use_container_width=True
            )

        else:

            st.info(
                "No customers found."
            )


        st.divider()


        # ------------------------------------------
        # CHAT HISTORY
        # ------------------------------------------

        st.subheader(
            "💬 Chat History"
        )

        response = requests.get(

            f"{API_URL}/chats"
        )

        chats = response.json()


        if chats:

            st.dataframe(

                chats,

                use_container_width=True
            )

        else:

            st.info(
                "No conversations found."
            )


    except Exception as e:

        st.error(
            f"Backend connection error: {e}"
        )
import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import pandas as pd

# Configure Gemini API
api_key = "AIzaSyDX3HE-dhk-0xUc7amKaIz8avJ6gpUFeGo"  # Replace with your actual API key
genai.configure(api_key=api_key)

# Initialize the Gemini model (Multimodal for OCR & Text Generation)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

def extract_text_from_image(image):
    """Extract text from an image using Gemini API."""
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG")
    img_bytes = img_bytes.getvalue()

    response = model.generate_content([
        "Extract all readable text from this image:",
        {"mime_type": "image/png", "data": img_bytes}
    ])
    
    return response.text if response.text else "No text found"

def generate_diet_plan(extracted_text, user_query):
    """Generate a diet plan based on extracted text and user input."""
    prompt = f"""
    Based on the following health details extracted from an image, generate a customized diet plan:
    {extracted_text}

    User Query: {user_query}

    Ensure the diet plan is structured in a **tabular format** with:
    - **Day** (1, 2, 3, etc.)
    - **Breakfast**
    - **Lunch**
    - **Snacks**
    - **Dinner**
    - **Hydration compulsory with varying litres of water accordinly**
     !! Warning remove index value frim the table
    Make sure the table does NOT contain any empty columns or unnecessary headers.Warning! generate only indian specifically south indian foods
    """

    response = model.generate_content(prompt)
    return response.text if response.text else "Unable to generate a diet plan."

def format_diet_plan_as_table(diet_plan_text):
    """Convert Gemini-generated text into a structured table."""
    # Split lines and filter only lines containing table data
    lines = diet_plan_text.split("\n")
    structured_data = [line.split("|") for line in lines if "|" in line]

    # Remove leading/trailing spaces in each cell & filter out empty rows
    structured_data = [[cell.strip() for cell in row if cell.strip()] for row in structured_data]

    if structured_data:
        # Ensure column names are unique and valid
        columns = structured_data[0]
        structured_data = structured_data[1:]  # Remove header row from data

        df = pd.DataFrame(structured_data, columns=columns)

        # Drop completely empty columns if any
        df = df.dropna(axis=1, how="all")

        return df
    return None

# Streamlit UI
st.set_page_config(page_title="Gemini AI Diet Chat", layout="wide")

st.title("🍏 Gemini AI Diet Chat - Personalized Meal Plans")
st.write("Upload an **image with health information**, ask questions, and get a structured diet plan.")

# Upload file
uploaded_file = st.file_uploader("📂 Upload an image", type=["png", "jpg", "jpeg"])

extracted_text = ""

if uploaded_file:
    # Display uploaded image
    st.image(uploaded_file, caption="🖼️ Uploaded Image", use_container_width=True)

    # Extract text from image
    with st.spinner("Extracting text from image... ⏳"):
        image = Image.open(uploaded_file)
        extracted_text = extract_text_from_image(image)

    # Display extracted text
    st.subheader("📜 Extracted Text:")
    st.text_area("Extracted Text", extracted_text, height=200)

# Chat Interface
st.subheader("💬 Chat with AI for Your Diet Plan")
user_query = st.text_input("Ask AI anything about your diet plan (e.g., 'Generate a 5-day plan'):")

if st.button("Generate Diet Plan"):
    if extracted_text and user_query:
        with st.spinner("Generating your personalized diet plan... 🍽️"):
            diet_plan_text = generate_diet_plan(extracted_text, user_query)
        
        # Convert diet plan into table
        diet_table = format_diet_plan_as_table(diet_plan_text)

        # Display structured diet plan
        st.subheader("🥗 Personalized Diet Plan:")
        if diet_table is not None:
            st.dataframe(diet_table)  # Use st.dataframe instead of st.table for better scrolling
        else:
            st.text_area("Diet Plan", diet_plan_text, height=400)

        # Download button
        st.download_button("⬇ Download Diet Plan", diet_plan_text, file_name="diet_plan.txt", mime="text/plain")

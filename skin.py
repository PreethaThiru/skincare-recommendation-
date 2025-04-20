import streamlit as st
import pandas as pd
from groq import Groq

# Load Datasets
@st.cache_data
def load_data():
    product_info = pd.read_csv('product_info.csv')
    reviews_files = [
        'reviews_0-250.csv', 'reviews_250-500.csv', 'reviews_500-750.csv', 
        'reviews_750-1250.csv', 'reviews_1250-end.csv'
    ]
    reviews_data = pd.concat([pd.read_csv(file) for file in reviews_files], ignore_index=True)
    return product_info, reviews_data

product_info, reviews_data = load_data()

# GROQ API Key
GROQ_API_KEY = "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"

# Function to generate explanations using GROQ API
def generate_explanation(user_input, product_name, brand_name):
    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = f"""
You are a skincare expert helping a customer understand why a specific product is suitable for their needs.
Please analyze the user's skincare concerns and the product details, and provide practical advice in simple, non-technical language. Also, provide a detailed technical analysis of how the product's ingredients and formulation address the user's concerns.

User's skincare concerns: {user_input}
Product details:
- Name: {product_name}
- Brand: {brand_name}

Please provide your response in this format:
1. Simple Summary: ( only 2- 3 points\lines explaining why this product is suitable)
2. Key Benefits: (1-2 bullet points of the product's key features and how they address the user's concerns)
3. How it Works: (Explain the technical details in 1 to 2 lines \ points of the product's formulation and ingredients)
4. Usage Tips: ( only 2 points Any specific instructions on how to use the product effectively)
"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[{
                    "role": "system",
                    "content": "You are a helpful skincare expert who translates product details into practical advice for customers."
                },
                {
                    "role": "user",
                    "content": prompt
                }],
            model="llama-3.1-70b-versatile",
            temperature=0.7,
            max_tokens=1000
        )
        return chat_completion.choices[0].message.content
    
    except Exception as e:
        return f"Error getting insights: {str(e)}"

# Function to generate a personalized routine
def generate_routine(user_input, top_products):
    client = Groq(api_key=GROQ_API_KEY)

    product_names = ', '.join([product['product_name'] for _, product in top_products.iterrows()])
    prompt = f"""
Based on the following products: {product_names}, and the user's skincare concerns: {user_input}, 
please generate a personalized skincare routine. The routine should:
1. Be in a logical order (cleanser, toner, serum, moisturizer, SPF, etc.)
2. Include product recommendations in each step (using the names of the recommended products)
3. Provide usage instructions for each product based on the user's skin type and concerns.

Please output the routine in a step-by-step format.
"""
    try:
        chat_completion = client.chat.completions.create(
            messages=[{
                    "role": "system",
                    "content": "You are a skincare expert generating personalized skincare routines."
                },
                {
                    "role": "user",
                    "content": prompt
                }],
            model="llama-3.1-70b-versatile",
            temperature=0.7,
            max_tokens=1500
        )
        return chat_completion.choices[0].message.content
    
    except Exception as e:
        return f"Error generating routine: {str(e)}"

# Streamlit App Layout
st.title("Personalized Skincare Recommendation System")

# Step 1: User Input for Product Type
st.header("Step 1: Choose your product type")
product_type = st.selectbox("Product Type", product_info['primary_category'].unique())

# Step 2: User Concern Input
st.header("Step 2: Tell us about your skincare concerns")
user_input = st.text_area("Describe your skincare concerns (e.g., 'I have oily skin and frequent breakouts.')")

# Step 3: Brand Preference (Optional)
st.header("Step 3: Select Preferred Brand (Optional)")
brand_input = st.selectbox("Preferred Brand (Leave blank for no preference)", ['Any'] + list(product_info['brand_name'].unique()))

# Step 4: Filter Products Based on User Input
def recommend_products(user_input, product_type, brand_input):
    # Filter products based on user's choice
    if brand_input != 'Any':
        filtered_products = product_info[
            (product_info['primary_category'] == product_type) & 
            (product_info['brand_name'] == brand_input)
        ]
    else:
        filtered_products = product_info[
            (product_info['primary_category'] == product_type)
        ]
    
    # Recommend top 3 products by rating
    top_products = filtered_products.sort_values(by='rating', ascending=False).head(3)
    
    # Generate explanations for each product
    recommendations = []
    for _, product in top_products.iterrows():
        product_desc = f"{product['product_name']} by {product['brand_name']} is priced at ${product['price_usd']} and rated {product['rating']}/5."
        explanation = generate_explanation(user_input, product['product_name'], product['brand_name'])
        recommendations.append((product_desc, explanation))
    
    return recommendations, top_products

# Function to safely extract sections
def get_section(text, section):
    """Extracts section from the explanation if it exists; otherwise returns a default message."""
    if section in text:
        return text.split(section)[1].strip()
    else:
        return "Information not available."

# Step 5: Display Recommendations and Explanations
if st.button("Get Recommendations"):
    st.subheader("Analysis Results")
    
    # Create columns for each product's explanation
    col1, col2, col3 = st.columns(3)

    recommendations, top_products = recommend_products(user_input, product_type, brand_input)
    
    # Check if recommendations list is empty
    if not recommendations:
        st.write("No products found for the selected filters.")
    else:
        # Displaying the products in columns with product names as headings
        with col1:
            st.markdown(f"### {recommendations[0][0]}")  # Product 1 name
            explanation = recommendations[0][1]
            st.write(f"**Simple Summary**: {get_section(explanation, 'Key Benefits:')}")
            st.write(f"**Key Benefits**: {get_section(explanation, 'How it Works:')}")
            st.write(f"**How it Works**: {get_section(explanation, 'Usage Tips:')}")
            st.write(f"**Usage Tips**: {get_section(explanation, 'Usage Tips:')}")

        # Repeat the same logic for col2 and col3
        if len(recommendations) > 1:
            with col2:
                st.markdown(f"### {recommendations[1][0]}")
                explanation = recommendations[1][1]
                st.write(f"**Simple Summary**: {get_section(explanation, 'Key Benefits:')}")
                st.write(f"**Key Benefits**: {get_section(explanation, 'How it Works:')}")
                st.write(f"**How it Works**: {get_section(explanation, 'Usage Tips:')}")
                st.write(f"**Usage Tips**: {get_section(explanation, 'Usage Tips:')}")
        
        if len(recommendations) > 2:
            with col3:
                st.markdown(f"### {recommendations[2][0]}")
                explanation = recommendations[2][1]
                st.write(f"**Simple Summary**: {get_section(explanation, 'Key Benefits:')}")
                st.write(f"**Key Benefits**: {get_section(explanation, 'How it Works:')}")
                st.write(f"**How it Works**: {get_section(explanation, 'Usage Tips:')}")
                st.write(f"**Usage Tips**: {get_section(explanation, 'Usage Tips:')}")
    
    # Step 6: Generate and Display the Routine
    st.subheader("Recommended Skincare Routine")
    routine = generate_routine(user_input, top_products)
    st.write(routine)

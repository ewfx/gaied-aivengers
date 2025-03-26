# 🚀 Project Name

**Gen AI Orchestrator for Email and Document Triage/Routing**

## 📌 Table of Contents
- [Introduction](#introduction)
- [Demo](#demo)
- [Inspiration](#inspiration)
- [Problem Statement](#problem-statement)
- [What It Does](#what-it-does)
- [How We Built It](#how-we-built-it)
- [Challenges We Faced](#challenges-we-faced)
- [How to Run](#how-to-run)
- [Tech Stack](#tech-stack)
- [Team](#team)

---

## 🎯 Introduction
The challenge we are dealing with is "Gen AI Orchestrator for Email and Document Triage/Routing". 

Managing large volumes of emails efficiently is a challenge for financial institutions. This project aims to automate email classification, attachment processing, and key information extraction to reduce manual effort and improve response times. By leveraging LLM, OCR, and AI Agents, the system accurately categorizes emails, extracts data from scanned documents, and optimizes email retrieval. This enhances operational efficiency and ensures faster, more accurate customer support.

## 🎥 Demo
🔗 [Live Demo](#) (if applicable)  
📹 [Video Demo](#) (if applicable)  
🖼️ Screenshots:


## 💡 Inspiration
The increasing volume of customer emails in the financial sector creates bottlenecks in processing and response times. Many emails contain attachments, multiple request types, and unstructured data, making manual handling inefficient and error-prone. This project was inspired by the need to automate email classification, extract key information, and streamline workflows using AI-driven solutions, ultimately improving customer experience and operational efficiency.

## ❔ Problem Statement

Commercial Bank Lending Service teams handle a large volume of servicing requests via email, often containing attachments, requiring manual triage by gatekeepers who classify request types, extract key details, and assign tasks to relevant teams. This manual process is time-consuming, error-prone, and inefficient at scale, leading to delays, increased workload, and inconsistencies in request handling. Develop an  intelligent AI system that can automatically classify emails, extract key information, and efficiently route requests to the appropriate teams to improve accuracy, efficiency, and turnaround time while reducing manual effort.

## ⚙️ What It Does
Our solution intelligently processes incoming emails by classifying them into predefined request types, extracting key details using OCR, and prioritizing them based on urgency using various AI agents and LLM's. It detects duplicate emails, ensures accurate intent recognition, and integrates seamlessly with backend for efficient decision-making. The system enables agents to review, validate, and take necessary actions, reducing manual effort and response times.

## 🛠️ How We Built It
1️⃣ **Large Language Models (LLMs)**
* DeepSeek Distill 70B – A high-performance language model used for understanding and classifying email content based on predefined request and sub-request types. It processes structured and unstructured text to determine the primary intent of an email.

* SambaNova – A multimodal AI model capable of extracting and analyzing text from various document formats like PDF, Excel, PPT, and images, enabling a comprehensive evaluation of email attachments.

2️⃣ **Backend Processing**

* Python – The core programming language for backend logic, handling email retrieval, document extraction, classification, and response generation. It integrates with various AI models and APIs to automate the workflow.

3️⃣ **Email Handling**

* Gmail API – A secure and efficient way to fetch emails, including metadata, email bodies, and attachments, directly from a Gmail inbox for processing. It enables programmatic access to user emails without requiring manual intervention.

* Email Parsing (email, re libraries) – These libraries help in extracting structured data from raw email content by removing unnecessary headers, signatures, and quoted replies for better classification.

4️⃣ **Document & Attachment Processing**

* PyMuPDF / PDFplumber – Libraries used to extract text from PDF attachments, enabling automated content processing for classification without requiring human intervention. They support structured and unstructured text extraction.

* python-pptx – A Python library that allows reading and extracting text from PowerPoint (PPT/PPTX) files, ensuring that relevant information from slides is included in the classification process.

* pandas– A widely used Python library for reading and manipulating Excel (XLSX) files, helping to extract tabular data, structured content, and text from spreadsheets for analysis.

* Pytesseract (OCR) – An optical character recognition (OCR) tool used to extract text from images (PNG/JPG), making it possible to process scanned documents and image-based attachments in emails.

5️⃣ **Classification & Data Processing**

* Predefined Request/Sub-request Types – A structured list of request types and sub-types that define various email categories, ensuring accurate classification based on real business use cases.

* Embedded Content Strategy – A processing mechanism that merges extracted text from attachments with the email body, ensuring both sources are considered in classification for improved accuracy.

## 🚧 Challenges We Faced
1. Handling Different Attachment Formats
2. Extracting Text from Images and Scanned PDFs
3. Efficient Email Retrieval
3. Categorizing Diverse Email Content
4. Handling Large-Scale Email Processing

Besides this, collaborating with the team and developing a solution within the given time frame was quite challenging for us, especially since some of the team members had other meetings scheduled at different times.


## 🏃 How to Run
1. Clone the repository  
   ```sh
   git clone https://github.com/ewfx/gaied-aivengers.git
   ```
2. Install dependencies  
   ```sh
   pip install streamlit google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client crewai pdfplumber python-pptx pandas pytesseract opencv-python pillow sentence-transformers faiss-cpu
   ```
3. Enable Gmail API and Download credentials.json
  
* Go to Google Cloud Console:
  
&emsp; &emsp;  Open Google Cloud Console.

&emsp; &emsp; Create a New Project:

&emsp; &emsp; &emsp; Click Select a project (top left).

&emsp; &emsp; &emsp; Click New Project, give it a name, and click Create.

* Enable Gmail API:
  
&emsp; &emsp; In the Cloud Console, search for Gmail API.

&emsp; &emsp; Click Enable.

* Create OAuth 2.0 Credentials:
  
&emsp; &emsp;  Go to APIs & Services → Credentials.

&emsp; &emsp; Click Create Credentials → OAuth client ID.

&emsp; &emsp; Select Application Type → Desktop App.

Click Create → Download JSON file → Rename it to credentials.json

* python quickstart.py to generate token

   
4. Run the project  
   ```sh
   streamlit run main.py 
   ```

## 🏗️ Tech Stack
- 🔹 Python
- 🔹 Frontend - Streamlit
- 🔹 LLM models - "sambanova/Llama-3.1-Swallow-8B-Instruct-v0.3", "groq/llama3-8b-8192"
- 🔹 Embedding model - SentenceTransformer("all-MiniLM-L6-v2")
- 🔹 Vector store - faiss-cpu
- 🔹 CrewAI (Agentic AI)
- 🔹 GMail API -Python client
- 🔹 Text Extraction
  
    &emsp;&emsp;&emsp; i. Pdfplumber  - Document

	 &emsp;&emsp;&emsp;ii. Pptx        -  Powerpoint

	 &emsp;&emsp;&emsp;iii. Pandas     -  Excel

	 &emsp;&emsp;&emsp;iv. PyTesseract - Image 

## 👥 Team
- **Gadde, Uma bhargavi** - [GitHub](https://github.com/umagadde) | [LinkedIn](https://www.linkedin.com/in/uma-bhargavi-gadde-2b70a824a/)
- **R, Pavithra** - [GitHub](https://github.com/PavithraGITHUB29) | [LinkedIn](https://www.linkedin.com/in/pavithra-ravikumar-a57979260)
- **Thopireddy, Harikishan reddy** - [GitHub](https://github.com/HarikishanReddy2004) | [LinkedIn](https://www.linkedin.com/in/thopireddy-harikishan-reddy)
- **Chennupati, Rishika K.** - [GitHub](https://github.com/rishi2332) | [LinkedIn](https://www.linkedin.com/in/rishika-krishna-ch/)
- **Y, Sristhi** - [GitHub](https://github.com/srishti09-12) | [LinkedIn](https://www.linkedin.com/in/srishti-yadav0912)

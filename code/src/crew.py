from crewai import Agent, Task, Crew, Process, LLM
from config import REQUEST_TYPES
from models import ClassificationResult, DuplicateCheckResult, ExtractionResult
from dotenv import load_dotenv
from extractor import extract_text_from_file

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Store previous email embeddings
email_embeddings = []
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def store_email_embedding(email_text, index, email_store):
    embedding = embedding_model.encode(email_text)
    email_embeddings.append(embedding)
    email_store.append((email_text, embedding))
    index.add(np.array([embedding]))


def retrieve_similar_emails(email_text, index, email_store, k=1):
    threshold=0.7
    if index.ntotal == 0:
        return []
    embedding = embedding_model.encode(email_text)
    distances, indices = index.search(np.array([embedding]), k)
    filtered_results = [
        email_store[i][0] for i, d in zip(indices[0], distances[0])
        if i < len(email_store) and d < threshold
    ]
    return filtered_results


load_dotenv()

llm = LLM(
    model="sambanova/Llama-3.1-Swallow-8B-Instruct-v0.3",
    temperature=0.2,
    max_tokens=100
)
llm3 = LLM(
    model="groq/llama3-8b-8192",
    temperature=0.2,
    max_tokens=100,
)


def create_agents():
    """Create and return CrewAI agents"""
    classification_agent = Agent(
        role="Email Classifier",
        goal=f"""
        Classify the email into one or more predefined request types and subrequest types.

        """,
        backstory="you are a classification agent",
        llm=llm,
        verbose=True
    )

    extraction_agent = Agent(
        role="Data Extractor",
        goal="Extract structured financial data based on the request type.",
        backstory="you are a data extraction agent",
        llm=llm3,
        verbose=True
    )

    duplicate_checker_agent = Agent(
        role="Duplicate Detector",
        goal="Detect duplicate emails and provide a reason if classified as a duplicate.",
        backstory="you are a duplicate detection agent",
        llm=llm,
        verbose=True
    )

    return classification_agent, extraction_agent, duplicate_checker_agent


def create_tasks(classification_agent, extraction_agent, duplicate_checker_agent):
    """Create and return CrewAI tasks"""
    classify_task = Task(
        description='''Identify the request type(s) from the email {email_text} and assign a primary request type based on the intent if multiple exist.
        Identify the *primary request type* if multiple requests exist.
        Ensure classification accuracy and return a *confidence score*.

        ## Request Types & Sub-Types:
        {REQUEST_TYPES}

        ## Rules for Multi-Intent Emails:
        1. If an email contains multiple request types, detect the *primary request type* based on the *main action required*.  
        2. List *secondary request types* separately.  
        3.  Assign a *confidence score (0-1)* to each classification.  
        4. If unsure, return the *most likely request type* with a confidence score.

        For example, the following email:

        **BORROWER: A
        DEAL NAME:
        Description: Facility Lender Share Adjustment
        ATLANTIC LLC
        TIC LLC $171.3MM 11-4-2022
        Effective 04-Feb-2025, the Lender Shares of facility TERM LOAN A-2 have been adjusted. Your share of the commitment was USD 5,518,249.19. It has been Increased to USD 5,542,963.55.**

        it can be classified as either "Adjustment" or "Money Movement Inbound." 
        But the primary request type will be "Money Movement Inbound" since the main ask is "funding the share."
        So the output will be:
        - Primary Request Type: Money Movement Inbound
        - Additional Request Types: Adjustment
        - Reason: The main ask is funding the share.

        ''',
        agent=classification_agent,
        output_pydantic=ClassificationResult,
        expected_output="Primary request type, subrequest type, confidence score, additional request types"
    )

    extract_task = Task(
        description="Extract structured loan servicing data from email body {email_text} and attachments.",
        agent=extraction_agent,
        output_pydantic=ExtractionResult,
        expected_output="Extracted feilds"
    )

    duplicate_task = Task(
        description="""
        Check if the email {email_text} is a duplicate based on prior received emails {retrieved_emails}.
        if *retrieved_emails* is empty then the email is not a duplicate.
        if *retrieved_emails* is not empty then check if the email is a duplicate or not.
        Consider the following:
        - high similarity in content.
        - Requests that are similar in intent.Format and indentation might be different
        - Contextual understanding of the request.
        Provide a reason why the email is a duplicate or not.
        """,
        agent=duplicate_checker_agent,
        output_pydantic=DuplicateCheckResult,
        expected_output="Duplicate flag, duplicate reason"
    )

    return classify_task, extract_task, duplicate_task


"""Process an email using CrewAI agents and tasks"""
classification_agent, extraction_agent, duplicate_checker_agent = create_agents()
classify_task, extract_task, duplicate_task = create_tasks(
    classification_agent, extraction_agent, duplicate_checker_agent
)
# Create a crew with the agents and tasks

crew1 = Crew(
    agents=[classification_agent],
    tasks=[classify_task, ],
    process=Process.sequential
)
crew2 = Crew(
    agents=[extraction_agent],
    tasks=[extract_task, ],
    process=Process.sequential
)
crew3 = Crew(
    agents=[duplicate_checker_agent],
    tasks=[duplicate_task, ],
    process=Process.sequential
)


def process_email_with_crew(email_data, index, email_store, previous_emails=None):
    # Get the base email text
    email_text = email_data.get("full_body") or email_data.get("snippet", "")
    retrieved_emails = retrieve_similar_emails(email_text, index, email_store)
    # Check for attachments and extract text if present
    if "attachments" in email_data and email_data["attachments"]:
        extracted_texts = []

        for attachment in email_data["attachments"]:
            try:
                # Assuming attachment has a 'path' field pointing to the saved file
                text = extract_text_from_file(attachment["path"])
                if text:
                    extracted_texts.append(text)
                    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
                    print(extracted_texts)
            except Exception as e:
                print(f"Failed to extract text from attachment: {e}")

        if extracted_texts:
            email_text = f"{email_text}\n\n--- ATTACHMENTS ---\n\n" + "\n\n".join(extracted_texts)
            print(email_text)
    # Prepare inputs for the crew
    store_email_embedding(email_text, index, email_store)
    inputs = {
        "email_text": email_text,
        "REQUEST_TYPES": REQUEST_TYPES,
        "retrieved_emails": retrieved_emails,
    }
    duplicate_flag=False
    duplicate_reason="The email content is unique and does not match any of the provided duplicate email examples."
    if(len(retrieved_emails)):
        duplicate_flag=True
        duplicate_reason="The email content is highly similar to other emails received, indicating a duplicate."




    # Execute the crew
    try:
        response1 = crew1.kickoff(inputs=inputs)
        response2 = crew2.kickoff(inputs=inputs)
        #response3 = crew3.kickoff(inputs=inputs)
        response = [response1, response2]
    except Exception as e:
        print(f"Error processing email: {e}")
        return None


    # Process and structure the results (rest of the function remains the same)
    # Process and structure the results
    result = {
        "classification": ClassificationResult(
            primary_request_type=response[0]["primary_request_type"],
            sub_request_type=response[0]["sub_request_type"],
            confidence_score=response[0]["confidence_score"],
            additional_request_types=response[0]["additional_request_types"],
            reason=response[0]["reason"],

        ),
        "extraction": ExtractionResult(
            request_type=response[1]["request_type"] or "Unknown",
            deal_name=response[1]["deal_name"] or "Unknown",
            borrower=response[1]["borrower"] or "Unknown",
            amount=response[1]["amount"],
            payment_date=response[1]["payment_date"],
            transaction_reference=response[1]["transaction_reference"]
        ),
        "duplicate": DuplicateCheckResult(
            duplicate_flag=duplicate_flag,
            duplicate_reason=duplicate_reason
        )

    }
    print(response)
    print(result)
    return result
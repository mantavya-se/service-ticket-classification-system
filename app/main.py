from fastapi import FastAPI, HTTPException
from app.schemas import TicketRequest, Priority, Category, TicketReview
from app.predict import predict_ticket
from app.insert_user_data import insert_data
from app.update_ticket import update_data
from app.get_tickets import get_all_tickets, get_specific_ticket
from rag.retrieve import retrieve as similarity_search

app = FastAPI()

@app.get("/")
async def root():
    return{"message": "Hello World!"}

@app.post("/analyze-ticket/")
def analyze_ticket(request: TicketRequest):
    category, confidence = predict_ticket(
        request.subcategory,
        request.description
    )
    text = f"{request.subcategory}. {request.description or ''}"
    similar = similarity_search(text)

    insert_data(
        ticket_id=request.ticket_id,
        subcategory=request.subcategory,
        priority=request.priority.value,
        description=request.description,
        predicted_category=str(category),
        predicted_confidence=float(confidence)
    )

    return {
        "query": text,
        "Category": category,
        "Confidence": confidence,
        "Similar Docs": similar
    }

@app.patch("/tickets/{ticket_id}/review")
def review_ticket(ticket_id: str, review: TicketReview):
    ticket_found = update_data(
        ticket_id = ticket_id,
        confirmed_category = review.confirmed_category.value
    )
    if not ticket_found:
        raise HTTPException(
            status_code=404,
            detail=f"Ticket '{ticket_id}' not found."
        )

        return {
            "ticket_id": ticket_id,
            "confirmed_category": review.confirmed_category.value,
            "reviewed": True,
        }

@app.get("/tickets")
def get_tickets():
    return get_all_tickets()

@app.get("/tickets/{ticket_id}")
def fetch_specific_ticket(ticket_id: str):
    ticket = get_specific_ticket(ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )
    
    return ticket
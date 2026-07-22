import { useEffect, useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL;

console.log("API URL:", API_URL);

const CATEGORIES = [
  "Hardware",
  "Software",
  "Access",
  "Network",
  "Security",
];

function formatCategory(category) {
  if (!category) {
    return "Not available";
  }

  if (Array.isArray(category)) {
    return category.join(", ");
  }

  return String(category)
    .replace(/^\['/, "")
    .replace(/'\]$/, "");
}

function isReviewed(ticket) {
  return Boolean(ticket.reviewed_at);
}

function AnalysisResult({ result }) {
  if (!result) {
    return null;
  }

  const category = result["Category"];
  const confidence = result["Confidence"];
  const similarDocs = result["Similar Docs"];

  return (
    <section>
      <h2>Analysis Result</h2>

      <p>
        <strong>Suggested Category:</strong>{" "}
        {formatCategory(category)}
      </p>

      <p>
        <strong>Confidence:</strong>{" "}
        {typeof confidence === "number"
          ? `${(confidence * 100).toFixed(2)}%`
          : "Not available"}
      </p>

      <h3>Recommended Knowledge Base Results</h3>

      {similarDocs?.length > 0 ? (
        similarDocs.map((article, index) => (
          <article
            key={`${article.file_name}-${article.section}-${index}`}
          >
            <h4>
              {article.subcategory ??
                article.file_name ??
                `Recommendation ${index + 1}`}
            </h4>

            <p>
              <strong>Category:</strong>{" "}
              {article.category ?? "Not available"}
            </p>

            <p>
              <strong>Section:</strong>{" "}
              {article.section ?? "Not available"}
            </p>

            {typeof article.similarity === "number" && (
              <p>
                <strong>Similarity:</strong>{" "}
                {(article.similarity * 100).toFixed(2)}%
              </p>
            )}

            <p>{article.chunk_text}</p>

            <hr />
          </article>
        ))
      ) : (
        <p>No knowledge-base recommendations were found.</p>
      )}
    </section>
  );
}

function TicketForm() {
  const [ticketId, setTicketId] = useState("");
  const [subcategory, setSubcategory] = useState("");
  const [priority, setPriority] = useState("");
  const [description, setDescription] = useState("");

  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        `${API_URL}/analyze-ticket/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ticket_id: ticketId,
            subcategory,
            priority,
            description,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : `Request failed with status ${response.status}`
        );
      }

      setResult(data);
    } catch (requestError) {
      setError(
        requestError.message ||
          "Unable to analyze the ticket."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section>
      <h1>Create Ticket</h1>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="ticket_id">Ticket ID</label>
          <br />

          <input
            id="ticket_id"
            type="text"
            value={ticketId}
            onChange={(event) =>
              setTicketId(event.target.value)
            }
            placeholder="Enter the ticket ID"
            required
          />
        </div>

        <br />

        <div>
          <label htmlFor="subcategory">
            Subject / Subcategory
          </label>
          <br />

          <textarea
            id="subcategory"
            value={subcategory}
            onChange={(event) =>
              setSubcategory(event.target.value)
            }
            placeholder="Example: Issues with Outlook"
            rows={3}
            cols={50}
            required
          />
        </div>

        <br />

        <div>
          <label htmlFor="priority">Priority</label>
          <br />

          <select
            id="priority"
            value={priority}
            onChange={(event) =>
              setPriority(event.target.value)
            }
            required
          >
            <option value="">Select a priority</option>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
            <option value="Critical">Critical</option>
          </select>
        </div>

        <br />

        <div>
          <label htmlFor="description">
            Description
          </label>
          <br />

          <textarea
            id="description"
            value={description}
            onChange={(event) =>
              setDescription(event.target.value)
            }
            placeholder="Describe the user's issue"
            rows={8}
            cols={50}
            required
          />
        </div>

        <br />

        <button type="submit" disabled={loading}>
          {loading
            ? "Analyzing..."
            : "Analyze Ticket"}
        </button>
      </form>

      {error && <p>{error}</p>}

      <AnalysisResult result={result} />
    </section>
  );
}

function TicketList({ onReviewTicket }) {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadTickets = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/tickets/`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            `Request failed with status ${response.status}`
        );
      }

      const loadedTickets = Array.isArray(data)
        ? data
        : data.tickets ?? [];

      console.log("Loaded tickets:", loadedTickets);

      setTickets(loadedTickets);
    } catch (requestError) {
      setError(
        requestError.message ||
          "Unable to load tickets."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
  }, []);

  if (loading) {
    return <p>Loading tickets...</p>;
  }

  return (
    <section>
      <h1>Tickets</h1>

      <button type="button" onClick={loadTickets}>
        Refresh Tickets
      </button>

      {error && <p>{error}</p>}

      {!error && tickets.length === 0 && (
        <p>No tickets found.</p>
      )}

      {tickets.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Ticket ID</th>
              <th>Subcategory</th>
              <th>Priority</th>
              <th>Predicted Category</th>
              <th>Confirmed Category</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {tickets.map((ticket) => {
              const reviewed = isReviewed(ticket);

              return (
                <tr key={ticket.ticket_id}>
                  <td>{ticket.ticket_id}</td>

                  <td>
                    {ticket.subcategory ??
                      "Not available"}
                  </td>

                  <td>
                    {ticket.priority ??
                      "Not available"}
                  </td>

                  <td>
                    {formatCategory(
                      ticket.predicted_category
                    )}
                  </td>

                  <td>
                    {reviewed
                      ? ticket.confirmed_category ??
                        "Not available"
                      : "Not corrected"}
                  </td>

                  <td>
                    {reviewed
                      ? "Reviewed"
                      : "Pending Review"}
                  </td>

                  <td>
                    <button
                      type="button"
                      onClick={() =>
                        onReviewTicket(
                          ticket.ticket_id
                        )
                      }
                    >
                      {reviewed
                        ? "View Review"
                        : "Review Ticket"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}

function TicketReview({ ticketId, onBack }) {
  const [ticket, setTicket] = useState(null);

  const [
    confirmedCategory,
    setConfirmedCategory,
  ] = useState("");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadTicket = async () => {
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch(
        `${API_URL}/tickets/${ticketId}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            `Request failed with status ${response.status}`
        );
      }

      const loadedTicket = data.ticket ?? data;

      console.log("Loaded ticket:", loadedTicket);

      setTicket(loadedTicket);

      setConfirmedCategory(
        loadedTicket.confirmed_category ??
          formatCategory(
            loadedTicket.predicted_category
          ) ??
          ""
      );
    } catch (requestError) {
      setError(
        requestError.message ||
          "Unable to load the ticket."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTicket();
  }, [ticketId]);

  const handleCorrection = async (event) => {
    event.preventDefault();

    if (!confirmedCategory) {
      setError("Select a confirmed category.");
      return;
    }

    setSaving(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch(
        `${API_URL}/tickets/${ticketId}/review`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            confirmed_category:
              confirmedCategory,
          }),
        }
      );

      const data = await response.json();

      console.log("PATCH response:", data);

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : `Request failed with status ${response.status}`
        );
      }

      const updatedTicket =
        data.ticket ??
        data.updated_ticket ??
        data;

      setTicket((currentTicket) => ({
        ...currentTicket,
        ...updatedTicket,
        confirmed_category:
          updatedTicket.confirmed_category ??
          confirmedCategory,
        reviewed_at:
          updatedTicket.reviewed_at ??
          new Date().toISOString(),
      }));

      setConfirmedCategory(
        updatedTicket.confirmed_category ??
          confirmedCategory
      );

      setMessage(
        "Ticket review saved successfully."
      );
    } catch (requestError) {
      setError(
        requestError.message ||
          "Unable to update the ticket."
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <p>Loading ticket...</p>;
  }

  if (!ticket) {
    return (
      <section>
        <button type="button" onClick={onBack}>
          Back to Tickets
        </button>

        <p>{error || "Ticket not found."}</p>
      </section>
    );
  }

  const reviewed = isReviewed(ticket);

  return (
    <section>
      <button type="button" onClick={onBack}>
        Back to Tickets
      </button>

      <h1>Review Ticket {ticketId}</h1>

      {error && <p>{error}</p>}
      {message && <p>{message}</p>}

      <div>
        <p>
          <strong>Ticket ID:</strong>{" "}
          {ticket.ticket_id}
        </p>

        <p>
          <strong>Subcategory:</strong>{" "}
          {ticket.subcategory ??
            "Not available"}
        </p>

        <p>
          <strong>Priority:</strong>{" "}
          {ticket.priority ?? "Not available"}
        </p>

        <p>
          <strong>Description:</strong>{" "}
          {ticket.description ??
            "Not available"}
        </p>

        <p>
          <strong>Predicted Category:</strong>{" "}
          {formatCategory(
            ticket.predicted_category
          )}
        </p>

        <p>
          <strong>Confidence:</strong>{" "}
          {typeof ticket.predicted_confidence ===
          "number"
            ? `${(
                ticket.predicted_confidence * 100
              ).toFixed(2)}%`
            : "Not available"}
        </p>

        <p>
          <strong>Review Status:</strong>{" "}
          {reviewed
            ? "Reviewed"
            : "Pending Review"}
        </p>

        <p>
          <strong>Confirmed Category:</strong>{" "}
          {reviewed
            ? ticket.confirmed_category ??
              "Not available"
            : "Not corrected"}
        </p>

        {reviewed && (
          <p>
            <strong>Reviewed At:</strong>{" "}
            {new Date(
              ticket.reviewed_at
            ).toLocaleString()}
          </p>
        )}
      </div>

      <hr />

      <form onSubmit={handleCorrection}>
        <label htmlFor="confirmed_category">
          Confirmed Category
        </label>

        <br />

        <select
          id="confirmed_category"
          value={confirmedCategory}
          onChange={(event) =>
            setConfirmedCategory(
              event.target.value
            )
          }
          required
        >
          <option value="">
            Select the correct category
          </option>

          {CATEGORIES.map((category) => (
            <option
              key={category}
              value={category}
            >
              {category}
            </option>
          ))}
        </select>

        <br />
        <br />

        <button type="submit" disabled={saving}>
          {saving
            ? "Saving..."
            : reviewed
              ? "Update Review"
              : "Save Review"}
        </button>
      </form>
    </section>
  );
}

function App() {
  const [page, setPage] = useState("create");

  const [
    selectedTicketId,
    setSelectedTicketId,
  ] = useState(null);

  const openTicketReview = (ticketId) => {
    setSelectedTicketId(ticketId);
    setPage("review");
  };

  const returnToTickets = () => {
    setSelectedTicketId(null);
    setPage("tickets");
  };

  return (
    <main>
      <nav>
        <button
          type="button"
          onClick={() => setPage("create")}
        >
          Create Ticket
        </button>

        <button
          type="button"
          onClick={() => setPage("tickets")}
        >
          View Tickets
        </button>
      </nav>

      <hr />

      {page === "create" && <TicketForm />}

      {page === "tickets" && (
        <TicketList
          onReviewTicket={openTicketReview}
        />
      )}

      {page === "review" &&
        selectedTicketId && (
          <TicketReview
            ticketId={selectedTicketId}
            onBack={returnToTickets}
          />
        )}
    </main>
  );
}

export default App;
# 📬 InboxOps

🚀 AI-powered workflow automation platform that converts **inbound emails** into **live, actionable dashboards** — built with [Postmark](https://postmarkapp.com/inbound) and LLMs.

---

## ✨ Highlights

- 📥 **Postmark Inbound Email Parsing** → clean JSON
- 🧠 **LLM-powered Summarization, Classification, Tags, Priority**
- 🗂️ Route to: Orders, Approvals, Support, HR, Enquiries
- 🖥️ Clean modular **dashboard UI with filters, pills, modals**
- 💬 **Built-in Enterprise AI Chatbot** for querying

---

## 🖼️ Screenshots

![Dashboard](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/timiacpzy73z78s5r1h5.png)

![Orders + Summary](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/j4znftj80mlvxrx4t0n6.png)

![Support Enquiries](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/5pqkbgafn845aj2mdjwq.png)

---

## 🛠️ Tech Stack

- **FastAPI** — Backend & APIs
- **Postmark** — Inbound Email Parsing
- **Gemini Flash (LLM)** — Summary, tags, criticality
- **SQLite + SQLAlchemy** — DB & ORM
- **Jinja2 + Tailwind CSS** — UI templates
- **Render.com** — Hosting (Demo)

---

## 🧠 AI Chat Demo

InboxOps includes a native AI chat modal that uses parsed email context to answer questions like:

- “Show recent approvals.”
- “Track order ODR-20240603...”
- “What is the trend in leave requests?”

![AI Chat](https://dev-to-uploads.s3.amazonaws.com/uploads/articles/zdfeb8jqv5qhisttxgj4.png)

---

## 🔗 Live Demo

🌐 [https://inboxops.render.com](https://inboxops.render.com)

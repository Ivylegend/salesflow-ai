# SalesFlow AI workflows

These import-ready workflows keep FastAPI as the source of truth. Configure the n8n container with `OPENAI_API_KEY`, `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `SALESFLOW_API_URL`, `N8N_WEBHOOK_SECRET`, and `CALCOM_BOOKING_URL` before activation.

Import and activate in this order: Hot Lead Follow-Up, Warm Lead Nurture, Appointment Event, then Lead Qualification. The API calls the production `salesflow-lead` webhook after committing a new lead.


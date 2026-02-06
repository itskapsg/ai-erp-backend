# 🏢 ORGANIZATION: JGandhi Tex ERP
**Location:** Surat, Gujarat, India
**Business Model:** Textile Agency (Commission Agent)
**Workflow:** Connects **Buyers** (Customers) ↔ **Sellers** (Suppliers). No inventory; manage orders & commissions.

# ⚙️ TECHNICAL ARCHITECTURE (The "Hybrid" Setup)
- **Server:** Ubuntu VPS (95.111.253.134).
- **Process Manager:** PM2 (Native) manages Backend & Frontend.
- **AI Agent:** "Gemini Operator" (Native Python).
- **Backend:** FastAPI on Port **54279**.
  - Dependencies: uvicorn, sqlalchemy, psycopg2-binary, python-jose, python-multipart.
  - Database: PostgreSQL.
- **Frontend:** React + Vite on Port **56000**.
  - Public Access: Binds to 0.0.0.0.

# 🧩 COMPLETED MODULES
1. **Authentication:** JWT (Admin, Manager, Accountant, Salesman).
2. **Partners:** Buyers/Sellers management.
3. **Orders:** Financial math fixed (Current + Outstanding > Limit = Block).
4. **Namaste (Visit Manager):**
   - Dashboard with cards.
   - "JAIN" diet triggers green badge.
   - Wizard for creating visits.

# 🚨 KNOWN ISSUES TO CHECK (Health Check Required)
1. **Database:** Verify connectivity (SELECT 1).
2. **Ports:** Confirm 54279, 56000 are listening on 0.0.0.0.
3. **Git:** Check for detached head or uncommitted changes.
4. **Pages:** Verify /namaste route loads correctly.
5. **Environment:** Verify new google-genai package is active.

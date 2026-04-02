## 🧩 Domains Overview

This system is organized using a **domain-based architecture**, where each app represents a specific business context. The goal is to isolate complexity, especially when dealing with multiple external systems and inconsistent data sources.

---

### 📊 `analytics`
Handles **data aggregation and reporting** across the system.

- Power BI–like outputs  
- Dashboards and metrics  
- Read-heavy queries  
- Cross-domain insights  

> Read-only oriented. Built on top of normalized/core data.

---

### 🥊 `arena`
Responsible for **competition management and orchestration**.

- Brackets generation  
- Seeding (ranking logic)  
- Fight order control  
- Interaction with Arena API  

> Contains real-time and operational logic for competitions.

---

### 👥 `entities`
Core domain for **people and organizations**.

- Athletes  
- Coaches  
- Teams  
- Federations  
- Identity resolution across systems  

> Central reference for all actors in the system.

---

### 🔗 `integration`
Handles all **external system communication**.

- API clients (gestão, arena, etc.)  
- Webhooks (incoming/outgoing)  
- Data ingestion and delivery  
- Retry and failure handling  

> Acts as an **anti-corruption layer**, isolating external inconsistencies.

---

### 🧪 `normalization`
Responsible for **data standardization (ETL layer)**.

- Field name normalization (`sportName` → `sport`)  
- Value mapping (`Freestyle`, `LIVRE` → `FS`)  
- Data cleaning and transformation rules  
- Mapping tables (DB-driven when needed)  

> Ensures internal consistency across inconsistent external sources.

---

### 🧾 `reports`
Manages **complex business workflows and official reporting**.

- Government processes (e.g. scholarships)  
- Multi-step validation flows  
- Report generation (including historical)  
- Status/state management  

> This is a **process-driven domain**, not just CRUD.

---

## 🔄 Data Flow Overview

The system follows a **controlled data flow** to ensure consistency and isolation between external systems and internal domains.

### 1. External Systems → Integration
- Data is received via APIs or webhooks  
- No assumptions are made about structure or consistency  

### 2. Integration → Normalization
- Raw data is transformed into standardized formats  
- Field names and values are mapped to internal conventions  

### 3. Normalization → Domains
- Clean, consistent data is passed to domain apps (`entities`, `arena`, `reports`, etc.)  
- Domains operate only on normalized data  

### 4. Domains → Analytics
- Processed and structured data is aggregated  
- Used for dashboards, reporting, and insights  

### 5. Domains → Integration (outgoing)
- When needed, data is sent back to external systems (e.g. Arena, gestão APIs)  
- Always formatted according to external requirements  

---

## 🧠 Design Principles

- **Domain isolation first**: each app owns its logic and rules  
- **External systems are unreliable**: always handled via `integration`  
- **Normalization is mandatory**: no raw external data leaks into domains  
- **Business logic > data structure**: focus on workflows and rules  
- **Scalable for future clients**: domains can evolve independently  
# Co-Lending FastAPI Backend - API Documentation

## Table of Contents
- [Overview](#overview)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Core Endpoints](#core-endpoints)
  - [Loan Allocation](#loan-allocation)
  - [Batch Processing](#batch-processing)
  - [Partner Management](#partner-management)
  - [System Health](#system-health)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Overview

The Co-Lending FastAPI Backend provides REST API endpoints for:
- Single loan allocation using weighted random selection
- Batch processing of multiple loans via Excel upload
- Partner and partnership management
- Real-time allocation with sub-100ms performance

## Base URL

```
http://localhost:8000
```

**Production:** Replace with your production domain

## Authentication

Currently, the API does not require authentication. For production deployment, implement:
- JWT token authentication
- API key authentication
- OAuth2 integration

---

## Core Endpoints

### Loan Allocation

#### Single Loan Allocation
Allocate a single loan to the optimal partner using weighted random selection.

**Endpoint:** `POST /api/allocate`

**Parameters:**
- `program_id` (query parameter): Program ID for allocation strategy (integer)

**Request Body:**
```json
{
  "loan_id": "string",
  "amount": 500000,
  "tenure": 24,
  "product_type": "PERSONAL_LOAN",
  "orig_rate": 0.165,
  "cibil_score": 750,
  "foir": 0.35,
  "ltr": 0.6
}
```

**Request Fields:**
| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| loan_id | string | Yes | Unique loan identifier | "LOAN_001" |
| amount | number | Yes | Loan amount in Rs | 500000 |
| tenure | integer | Yes | Loan tenure in months | 24 |
| product_type | string | Yes | Type of loan product | "PERSONAL_LOAN" |
| orig_rate | number | Yes | Originator rate (decimal) | 0.165 |
| cibil_score | integer | Yes | CIBIL score (300-900) | 750 |
| foir | number | Yes | Fixed Obligation to Income Ratio | 0.35 |
| ltr | number | No | Loan to Revenue ratio | 0.6 |

**Success Response (200 OK):**
```json
{
  "loan_id": "LOAN_001",
  "recommended_partner": {
    "partner_id": 4,
    "name": "Lender C",
    "profit_score": 0.0386,
    "selection_score": 38461538.46,
    "approval_prob": 0.78
  },
  "all_options": [
    {
      "partner_id": 2,
      "name": "Lender A", 
      "profit_score": 0.0333,
      "selection_score": 64102564.10,
      "approval_prob": 0.78
    },
    {
      "partner_id": 3,
      "name": "Lender B",
      "profit_score": 0.0359,
      "selection_score": 51282051.28,
      "approval_prob": 0.78
    }
  ],
  "reasoning": "Selected based on weighted random algorithm with participation: 35.0%",
  "processing_time_ms": 3.545
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "No eligible partnerships found for this loan"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/allocate?program_id=1" \
-H "Content-Type: application/json" \
-d '{
  "loan_id": "LOAN_001",
  "amount": 500000,
  "tenure": 24,
  "product_type": "PERSONAL_LOAN",
  "orig_rate": 0.165,
  "cibil_score": 750,
  "foir": 0.35,
  "ltr": 0.6
}'
```

---

### Batch Processing

#### Upload Excel File
Upload an Excel file containing multiple loans for batch processing.

**Endpoint:** `POST /api/batch-upload`

**Parameters:**
- `program_id` (query parameter): Program ID (default: 1)

**Request:** Multipart form data
- `file`: Excel file (.xlsx, .xls)

**Excel File Format:**
Required columns:
| Column | Description | Example |
|--------|-------------|---------|
| client_loan_id | Unique loan ID | LOAN_001 |
| loan_amount | Amount in Rs | 500000 |
| cibil_score | CIBIL score | 750 |
| loan_foir | FOIR ratio | 0.35 |
| interest_rate | Rate in % or decimal | 16.5 or 0.165 |
| product_type | Product type | PERSONAL_LOAN |
| ltr | LTR ratio (optional) | 0.6 |

**Success Response (200 OK):**
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_loans": 100,
  "status": "UPLOADED",
  "estimated_time_min": 2
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/batch-upload?program_id=1" \
-F "file=@loans.xlsx"
```

#### Start Batch Processing
Begin processing uploaded batch of loans.

**Endpoint:** `POST /api/batch-process/{batch_id}`

**Path Parameters:**
- `batch_id`: Batch ID from upload response

**Success Response (200 OK):**
```json
{
  "message": "Processing completed",
  "batch_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/batch-process/550e8400-e29b-41d4-a716-446655440000"
```

#### Get Batch Status
Check the status of batch processing.

**Endpoint:** `GET /api/batch-status/{batch_id}`

**Path Parameters:**
- `batch_id`: Batch ID

**Success Response (200 OK):**
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "COMPLETED",
  "progress": 100,
  "total_loans": 100,
  "processed_loans": 98,
  "failed_loans": 2,
  "estimated_completion": null
}
```

**Status Values:**
- `UPLOADED`: File uploaded, ready for processing
- `PROCESSING`: Currently processing loans
- `COMPLETED`: Processing finished
- `FAILED`: Processing failed

#### Download Batch Results
Download processed results as Excel file.

**Endpoint:** `GET /api/batch-download/{batch_id}`

**Path Parameters:**
- `batch_id`: Batch ID

**Success Response:** Excel file download

**Result File Columns:**
- All original columns
- `status`: SUCCESS/ERROR
- `selected_partner`: Partner name
- `selected_partner_id`: Partner ID
- `approval_probability`: Approval probability
- `profit_score`: Combined profit score
- `selection_score`: Selection algorithm score
- `reasoning`: Algorithm reasoning
- `processing_time_ms`: Processing time
- `error_message`: Error details (if failed)

---

### Partner Management

#### List Partners
Get list of all active lending partners.

**Endpoint:** `GET /api/partners`

**Query Parameters:**
- `orig_id` (optional): Filter by originator ID

**Success Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "YUBI",
    "type": "YUBI",
    "active": true
  },
  {
    "id": 2,
    "name": "Lender A",
    "type": "EXTERNAL", 
    "active": true
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/partners"
```

#### Create Partner
Add a new lending partner.

**Endpoint:** `POST /api/partners`

**Request Body:**
```json
{
  "name": "New Lender",
  "type": "EXTERNAL"
}
```

**Partner Types:**
- `YUBI`: Internal YUBI partner
- `EXTERNAL`: External lending partner
- `OWN_BOOK`: Own book lending

**Success Response (200 OK):**
```json
{
  "id": 5,
  "name": "New Lender",
  "type": "EXTERNAL",
  "active": true
}
```

#### List Partnerships
Get co-lending partnerships with filtering options.

**Endpoint:** `GET /api/partnerships`

**Query Parameters:**
- `orig_id` (optional): Filter by originator ID
- `partner_id` (optional): Filter by partner ID  
- `active_only` (optional): Show only active partnerships (default: true)

**Success Response (200 OK):**
```json
[
  {
    "id": 1,
    "orig_id": 1,
    "partner_id": 2,
    "min_amount": 50000,
    "max_amount": 10000000,
    "products": ["PERSONAL_LOAN", "BUSINESS_LOAN"],
    "monthly_limit": 50000000,
    "service_fee": 0.018,
    "cost_funds": 0.085,
    "active": true,
    "partner_name": "Lender A"
  }
]
```

#### Create Partnership
Create new co-lending partnership.

**Endpoint:** `POST /api/partnerships`

**Request Body:**
```json
{
  "orig_id": 1,
  "partner_id": 2,
  "min_amount": 50000,
  "max_amount": 5000000,
  "products": ["PERSONAL_LOAN"],
  "rate_formula": {
    "participation": 0.30
  },
  "monthly_limit": 30000000,
  "service_fee": 0.020,
  "cost_funds": 0.088
}
```

**Request Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| orig_id | integer | Yes | Originator partner ID |
| partner_id | integer | Yes | Lender partner ID |
| min_amount | number | Yes | Minimum loan amount |
| max_amount | number | Yes | Maximum loan amount |
| products | array | Yes | Supported product types |
| rate_formula | object | Yes | Rate calculation config |
| monthly_limit | number | Yes | Monthly allocation limit |
| service_fee | number | Yes | Service fee rate |
| cost_funds | number | Yes | Cost of funds rate |

#### Update Partnership
Update existing partnership configuration.

**Endpoint:** `PUT /api/partnerships/{partnership_id}`

**Path Parameters:**
- `partnership_id`: Partnership ID

**Request Body:** (partial updates supported)
```json
{
  "monthly_limit": 40000000,
  "service_fee": 0.022,
  "active": true
}
```

**Success Response (200 OK):**
```json
{
  "message": "Partnership updated successfully",
  "partnership_id": 1
}
```

---

### System Health

#### Health Check
Check API health status.

**Endpoint:** `GET /health`

**Success Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "co-lending-backend"
}
```

#### Root Information
Get API information and links.

**Endpoint:** `GET /`

**Success Response (200 OK):**
```json
{
  "message": "Co-Lending FastAPI Backend",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

---

## Error Handling

### Standard HTTP Status Codes

| Code | Description | When Used |
|------|-------------|-----------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid input data |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "cibil_score"],
      "msg": "ensure this value is greater than 300",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

**No Eligible Partners (400):**
```json
{
  "detail": "No eligible partnerships found for this loan"
}
```

**Batch Not Found (404):**
```json
{
  "detail": "Batch not found"
}
```

---

## Rate Limiting

Currently no rate limiting implemented. For production, consider:
- Per-IP rate limiting
- Per-user/API key limits
- Different limits for different endpoints

---

## Examples

### Complete Workflow Example

```bash
# 1. Check API health
curl -X GET "http://localhost:8000/health"

# 2. Get available partners
curl -X GET "http://localhost:8000/api/partners"

# 3. Single loan allocation
curl -X POST "http://localhost:8000/api/allocate?program_id=1" \
-H "Content-Type: application/json" \
-d '{
  "loan_id": "LOAN_001",
  "amount": 500000,
  "tenure": 24,
  "product_type": "PERSONAL_LOAN",
  "orig_rate": 0.165,
  "cibil_score": 750,
  "foir": 0.35,
  "ltr": 0.6
}'

# 4. Batch upload
curl -X POST "http://localhost:8000/api/batch-upload?program_id=1" \
-F "file=@loans.xlsx"

# 5. Start batch processing (use batch_id from step 4)
curl -X POST "http://localhost:8000/api/batch-process/BATCH_ID"

# 6. Check batch status
curl -X GET "http://localhost:8000/api/batch-status/BATCH_ID"

# 7. Download results when completed
curl -X GET "http://localhost:8000/api/batch-download/BATCH_ID" -o results.xlsx
```

### Python Client Example

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# Single loan allocation
loan_data = {
    "loan_id": "LOAN_001",
    "amount": 500000,
    "tenure": 24,
    "product_type": "PERSONAL_LOAN", 
    "orig_rate": 0.165,
    "cibil_score": 750,
    "foir": 0.35,
    "ltr": 0.6
}

response = requests.post(
    f"{BASE_URL}/api/allocate?program_id=1",
    json=loan_data
)

if response.status_code == 200:
    result = response.json()
    print(f"Selected Partner: {result['recommended_partner']['name']}")
    print(f"Processing Time: {result['processing_time_ms']}ms")
else:
    print(f"Error: {response.json()['detail']}")

# Batch processing
files = {"file": open("loans.xlsx", "rb")}
upload_response = requests.post(
    f"{BASE_URL}/api/batch-upload?program_id=1",
    files=files
)

if upload_response.status_code == 200:
    batch_id = upload_response.json()["batch_id"]
    
    # Start processing
    process_response = requests.post(
        f"{BASE_URL}/api/batch-process/{batch_id}"
    )
    
    # Check status
    status_response = requests.get(
        f"{BASE_URL}/api/batch-status/{batch_id}"
    )
    
    print(f"Batch Status: {status_response.json()['status']}")
```

---

## Interactive Documentation

The API provides interactive documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Use these interfaces to:
- Test endpoints directly
- View request/response schemas
- Download OpenAPI specification

---

## Production Deployment

For production deployment:

1. **Environment Variables:**
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost/db"
   export REDIS_URL="redis://localhost:6379"
   export SECRET_KEY="your-secret-key"
   ```

2. **Security Headers:**
   - Enable HTTPS
   - Add authentication
   - Implement rate limiting
   - Add CORS configuration

3. **Monitoring:**
   - Add logging and metrics
   - Health check endpoints
   - Performance monitoring

4. **Scaling:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

---

*This documentation covers the Co-Lending FastAPI Backend v1.0.0*
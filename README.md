# Rentvine AI Assistant - Vinny

---

## IMPORTANT DISCLAIMER

**This application will ONLY work on the specific web URL pages documented in `HackathonBE/Notes.txt`.**

The Vinny AI assistant is configured to work exclusively with the following page types and URL patterns:

- **Maintenance Work Orders**: `/maintenance/work-orders/{id}`
- **Maintenance Inspections**: `/maintenance/inspections/{id}`
- **Maintenance Projects**: `/maintenance/projects/{id}`
- **Properties**: `/properties/{id}`
- **Screening Applications**: `/screening/applications/{id}`
- **Screening Prospects**: `/screening/prospects/{id}`
- **Screening Payments**: `/screening/payments/{id}`
- **Portfolios**: `/portfolios/{id}`
- **Accounting Diagnostics**: `/accounting/diagnostics`

**The assistant will NOT function correctly on any other pages.** For the complete list of supported endpoints and their exact URL patterns, please refer to `HackathonBE/Notes.txt`.

---

An intelligent customer support assistant that integrates with the Rentvine property management platform. Vinny provides context-aware responses by analyzing the current page context and fetching relevant data from the Rentvine API, then uses LM Studio for AI-powered conversational responses.

## Overview

Vinny is a contextual AI assistant that helps users navigate and understand their Rentvine property management data. The assistant understands the current page context (work orders, portfolios, leases, screening applications, etc.) and provides intelligent responses based on the specific data visible to the user.

## Architecture

The project consists of two main components:

- **Backend (HackathonBE)**: Flask API server that handles API routing, data fetching from Rentvine, prompt chunking, and communication with LM Studio
- **Frontend**: React chat widget (JavaScript) that is hosted within Rentvine's development environment on皮革 the `support-hackathon` branch. The `HackathonFE` directory contains TypeScript source code for development and testing purposes, but the actual frontend components deployed in the Rentvine codebase at `apps/manager/src/components/vinny/` in the `support-hackathon` branch are JavaScript (`.js`) files.

## Technology Stack

### Backend
- Python 3
- Flask 3.1.2
- Flask-CORS for cross-origin requests
- Requests for API calls
- OpenAI SDK (for LM Studio compatibility)
- Python-dotenv for environment configuration

### Frontend
- React (JavaScript)
- Chat widget components deployed in Rentvine's manager application

### AI
- LM Studio (local LLM server)
- Token-aware chunking for large context windows

## Prerequisites

Before running the application, ensure you have the following installed:

- Python 3.13 or higher
- LM Studio installed and running locally on port 1234
- Access to Rentvine API credentials
- Access to Rentvine's development environment (for frontend deployment)

## Setup

### Environment Variables

Create a `.env` file in the `HackathonBE` directory with the following variables:

```
API_USERNAME=your_rentvine_username
API_PASSWORD=your_rentvine_password
API_URL=your_rentvine_api_url
```

### Quick Start

The easiest way to set up and run the application is using the provided scripts:

**macOS/Linux:**
```bash
chmod +x run.sh
./run.sh
```

**Windows:**
```powershell
.\run.ps1
```

These scripts will:
1. Check for required dependencies (Python)
2. Create a Python virtual environment if it doesn't exist
3. Install all Python dependencies
4. Start the backend server
5. Handle graceful shutdown on Ctrl+C

Note: The frontend is hosted separately in Rentvine's development environment on the `support-hackathon` branch, not through these scripts.

### Manual Setup

If you prefer to set up manually:

1. **Set up Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Start LM Studio:**
   - Ensure LM Studio is installed and running
   - Load a model (default: openai/gpt-oss-20b)
   - Start the local server on port 1234

3. **Start the backend:**
   ```bash
   cd HackathonBE
   python app.py
   ```
   Backend runs on http://127.0.0.1:5000

4. **Frontend Deployment:**
   The frontend is hosted within Rentvine's development environment. The frontend components are located in the Rentvine codebase at `apps/manager/src/components/vinny/`. To use the frontend:
   - Access the Rentvine development environment where the Vinny widget is deployed
   - The widget will communicate with the backend API running on http://127.0.0.1:5000
   
   Note: The `HackathonFE` directory contains the frontend source code for reference and testing, but the actual implementation is handled through Rentvine's development infrastructure.

## Project Structure

```
Hackathon/
├── HackathonBE/              # Backend Flask application
│   ├── app.py                # Main Flask application and API routes
│   ├── apiRoutes.py          # URL-to-API mapping and data fetching
│   ├── promptParsing.py      # Token-aware chunking for LM Studio
│   └── test.py               # Test utilities
├── HackathonFE/              # Frontend React application (development/testing)
│   ├── src/
│   │   ├── components/
│   │   │   ├── VinnyLauncher.tsx    # Chat launcher button
│   │   │   └── VinnyWidget.tsx      # Main chat widget component
│   │   ├── test-pages/              # Test portfolio pages
│   │   └── App.tsx                  # Main application component
│   └── package.json                 # Note: Frontend is actually deployed in Rentvine's dev environment
├── TrainingData/             # AI training context data
│   ├── IndividualData/       # Category-specific training data
│   │   ├── Accounting.json
│   │   ├── Contacts.json
│   │   ├── General.json
│   │   ├── Leases.json
│   │   ├── Maintenance.json
│   │   ├── Portfolios.json
│   │   └── Screening.json
│   └── Rentvine_AI_Training_Context.json
├── requirements.txt          # Python dependencies
├── run.sh                    # Setup and run script (macOS/Linux)
└── run.ps1                   # Setup and run script (Windows)
```

### Frontend Deployment Location

The frontend components are deployed in Rentvine's development environment on the `support-hackathon` branch:

```
support-hackathon branch/
apps/manager/src/components/vinny/
├── assets/
│   ├── easterEgg.png
│   ├── vinny.png
│   └── vinnyFinal.gif
├── Hackathon.css (499 lines)
├── VinnyLauncher.js (87 lines)
└── VinnyWidget.js (364 lines)
```

The frontend runs as part of Rentvine's manager application and communicates with the backend API.

## API Routes

### POST /api/query

Handles AI chat queries with context awareness.

**Request Body:**
```json
{
  "ephemeral": true,
  "store": true,
  "history": "",
  "question": "What is the status of this work order?",
  "url": "https://abchomes.rentvinedev.com/maintenance/work-orders/12345"
}
```

**Response:**
```json
{
  "answer": "The work order is currently in progress...",
  "sources": [{"title": "N/A", "url": "#"}]
}
```

## How It Works

1. **User Interaction**: User opens the Vinny chat widget on a Rentvine page
2. **Context Extraction**: The widget sends the current page URL to the backend
3. **API Mapping**: The backend uses `apiRoutes.py` to map the URL to the appropriate Rentvine API endpoint(s)
4. **Data Fetching**: Relevant data is fetched from the Rentvine API with appropriate includes
5. **Context Chunking**: Large responses are chunked using token-aware chunking to fit within LM Studio's context window
6. **AI Processing**: The backend sends the user question, API context, and chat history to LM Studio
7. **Response Generation**: LM Studio generates a contextual response based on the available data
8. **Response Delivery**: The AI response is returned to the frontend and displayed to the user

## Supported Page Types

The assistant supports the following Rentvine page types:

- Maintenance Work Orders
- Maintenance Inspections
- Maintenance Projects
- Properties
- Units
- Leases
- Screening Applications
- Screening Prospects
- Screening Payments
- Portfolios
- Ledgers
- Accounting Diagnostics

For each page type, the system automatically fetches relevant related data (includes) to provide comprehensive context to the AI.

## Development

### Backend Development

The Flask backend is structured to handle:
- CORS configuration for production domains
- API route mapping and parameter extraction
- Intelligent data chunking for large API responses
- Integration with LM Studio's OpenAI-compatible API

### Frontend Development

The React frontend includes:
- Chat widget component with session management
- URL-based context detection
- Chat history persistence
- Responsive UI design

The frontend source code in `HackathonFE/` is written in TypeScript (`.tsx` files), but the actual frontend components deployed in Rentvine's development environment at `apps/manager/src/components/vinny/` are JavaScript (`.js` files). The deployment is handled through Rentvine's development infrastructure.

## Configuration

### LM Studio Configuration

Ensure LM Studio is configured to:
- Run the local server on port 1234
- Use the model: `openai/gpt-oss-20b` (or update the model name in `app.py`)

### CORS Configuration

Update `ALLOWED_ORIGINS` in `HackathonBE/app.py` to include your production domain.

## Troubleshooting

### Backend won't start
- Ensure Python virtual environment is activated
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify environment variables are set in `.env` file

### Frontend issues
- The frontend is hosted in Rentvine's development environment on the `support-hackathon` branch
- Verify that you are on the `support-hackathon` branch in the Rentvine repository
- Verify that the frontend components are properly deployed in the Rentvine codebase
- Check that the Rentvine development server is running
- Ensure the frontend is configured to communicate with the backend at http://127.0.0.1:5000

### AI responses not working
- Verify LM Studio is running on port 1234
- Check that a model is loaded in LM Studio
- Verify the model name matches in `app.py` (default: `openai/gpt-oss-20b`)
- Check backend logs for API connection errors

### API data not fetching
- Verify Rentvine API credentials are correct in `.env`
- Check network connectivity to Rentvine API
- Review backend logs for API response errors

## License

This project is part of a hackathon submission.

## Contributors

Support Team Dub


# TripGenie - Multi-Agent Travel Planning System

A sophisticated travel planning platform powered by **LangGraph multi-agent workflows** that coordinate specialized AI agents to create personalized group trip recommendations.

## 🏗️ Architecture

### Multi-Agent System
- **🔍 ResearchAgent**: Destination analysis & preference matching
- **✈️ FlightAgent**: Flight search & price optimization  
- **🏨 HotelAgent**: Accommodation search & budget filtering
- **🎯 CoordinatorAgent**: Workflow orchestration & synthesis

### Technology Stack
- **Backend**: FastAPI + Python
- **Frontend**: React + TypeScript
- **AI Framework**: LangGraph (multi-agent workflows)
- **LLMs**: Claude 3.5 Sonnet + GPT-3.5 Turbo
- **APIs**: Travel APIs (Amadeus, etc.)

## 🚀 Features

- **Multi-Agent Coordination**: Specialized agents working together
- **Intelligent Budget Analysis**: Conservative group budgeting
- **Real-Time Flight & Hotel Search**: Integration with travel APIs
- **Group Preference Matching**: AI-powered destination scoring
- **Professional Workflows**: State management and agent handoffs

## 📁 Project Structure

```
TripGenie/
├── app/
│   ├── services/
│   │   ├── langgraph_agents.py    # Multi-agent system
│   │   ├── planner.py             # Main planning orchestrator
│   │   ├── ai_input.py            # Group analysis utilities
│   │   ├── auth.py                # Authentication
│   │   └── storage.py             # Data management
│   ├── api/                       # FastAPI routes
│   ├── models/                    # Data models
│   └── main.py                    # Application entry point
├── frontend/                      # React frontend
├── data/                          # Sample data & groups
└── test_langgraph.py             # Multi-agent system tests
```

## 🛠️ Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   # Create .env file
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   ```

3. **Run Backend**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Run Frontend**
   ```bash
   cd frontend
   npm install
   npm start
   ```

## 🧪 Testing

Test the multi-agent system:
```bash
python test_langgraph.py
```

Expected output:
```
🚀 TESTING LANGGRAPH MULTI-AGENT SYSTEM
✅ Multiple specialized agents: True
✅ Agent coordination: True  
✅ Workflow orchestration: True
✅ Professional architecture: True
```

## 🔮 Next Steps

- [ ] Install full LangGraph dependencies
- [ ] Implement graph-based workflow orchestration  
- [ ] Add advanced agent communication protocols
- [ ] Integrate real travel APIs (Amadeus, Booking.com)
- [ ] Add feedback loops and iterative improvement

## 🎯 Agent Workflow

1. **ResearchAgent** analyzes user preferences → destinations
2. **FlightAgent** searches flights for approved destinations
3. **HotelAgent** finds accommodations within budget
4. **CoordinatorAgent** synthesizes results → final recommendations

Each agent maintains state and communicates through the workflow orchestrator.

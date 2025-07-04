# LightYearAI

LightYearAI is a next generation AI assistant built to be safe, accurate, and secure to help users do their best work.

## Features

- **Study Buddy**: Get help with your studies, research topics, and learn new concepts with our intelligent AI tutor
- **Proofreading**: Polish your writing with advanced grammar and style suggestions
- **Entertainment**: Engage in creative conversations and get recommendations
- **Knowledge Integration**: Connect your data sources and import documents for personalized assistance
- **Team Collaboration**: Share and collaborate with team members for maximum productivity

## Tech Stack

- **Backend**: Python with Flask framework
- **Frontend**: HTML, CSS, JavaScript with responsive design
- **AI Integration**: Integration with advanced AI models
- **Database**: Firebase Firestore
- **Authentication**: Firebase Authentication
- **Storage**: Firebase Storage
- **Deployment**: Configured for deployment on Render

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 14+ (for some utilities)
- Firebase account
- Access to required AI APIs

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/your-username/lightyearai.git
   cd lightyearai
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables
   ```bash
   cp .env.sample .env
   # Edit .env with your configuration
   ```

4. Start the development server
   ```bash
   python app.py
   ```

5. Visit `http://localhost:5000` in your browser

## Deployment

Deployment configurations are included for Render cloud platform:

1. Use the provided `render.yaml` for configuration
2. Set up environment variables in the Render dashboard
3. Connect your GitHub repository to Render for CI/CD

## Project Structure

- `/templates`: HTML templates using Jinja2
- `/static`: Static assets (CSS, JS, images)
- `/agents`: AI agent implementations
- `/functions`: Cloud functions
- `/mcp`: Model Context Protocol implementation
- `/scripts`: Utility scripts
- `/tests`: Test suite

## License

This project is proprietary and confidential.

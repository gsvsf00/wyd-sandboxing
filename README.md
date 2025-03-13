# WydBot

A modern desktop application for game automation with a clean, responsive UI using Python and CustomTkinter.

![WydBot Logo](app/resources/images/logo.png)

## 🌟 Features

- **Secure Authentication**: User authentication with MongoDB
- **Account Management**: User registration, login, and subscription management
- **Game Automation**: Intelligent bot for game automation using YOLO trained models
- **Sandbox Environment**: Game launching with sandbox protection
- **Network Masking**: Hide bot activity with network masking
- **Modern UI**: Clean, responsive interface with dark/light mode
- **Dashboard**: Statistics and bot previews
- **Settings Management**: Customizable application settings

## 📋 Requirements

- Python 3.8+
- MongoDB (local or Atlas)
- See `requirements.txt` for detailed dependencies

## 🚀 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/gsvsf00/wyd-sandboxing.git
   cd wydbot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv myenv
   # On Windows
   myenv\Scripts\activate
   # On macOS/Linux
   source myenv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   # Copy the example .env file
   cp .env.example .env
   # Edit the .env file with your configuration
   ```

5. Run the application:
   ```bash
   python main.py
   ```

## 🔧 Configuration

WydBot uses a combination of configuration files and environment variables:

1. Create a `.env` file in the root directory based on `.env.example`
2. Set your MongoDB connection string and other sensitive information in the `.env` file
3. Application settings can be configured through the UI or by editing the config files

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| MONGODB_CONNECTION_STRING | MongoDB connection string | mongodb://localhost:27017 |
| APP_DEBUG | Enable debug mode | false |
| APP_THEME | UI theme (dark/light) | dark |
| APP_LANGUAGE | Application language | en |
| USE_PROXY | Enable proxy for network connections | false |
| PROXY_HOST | Proxy server host | |
| PROXY_PORT | Proxy server port | 0 |
| BOT_DEFAULT_INTERVAL | Default interval for bot actions (seconds) | 1.0 |
| BOT_HEALTH_CHECK_INTERVAL | Interval for bot health checks (seconds) | 5.0 |

## 🏗️ Architecture

WydBot follows a modern architecture with clear separation of concerns:

- **Model-View-ViewModel (MVVM)**: Separates UI from business logic
- **Component-Based Architecture**: Reusable UI components
- **Service-Oriented Architecture**: Core functionality exposed as services
- **Event-Driven Architecture**: Components communicate via events

For more details, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 📁 Project Structure

```
wydbot/
├── app/                  # Application code
│   ├── core/             # Core application code
│   ├── models/           # Data models
│   ├── services/         # Application services
│   ├── ui/               # User interface code
│   │   ├── components/   # Reusable UI components
│   │   └── frames/       # Application frames/screens
│   └── utils/            # Utility functions
├── config/               # Configuration files
├── logs/                 # Application logs
├── cache/                # Cache files
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore file
├── main.py               # Application entry point
├── requirements.txt      # Dependencies
└── README.md             # This file
```

## 🔒 Security

- Sensitive information is stored in environment variables, not in the code
- Passwords are securely hashed
- MongoDB connection uses secure authentication
- Network masking for bot activities

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Contact

For questions or support, please open an issue on GitHub or contact the maintainer.

---

**Note**: This application is for educational purposes only. Use responsibly and in accordance with the terms of service of any games or platforms you interact with. 
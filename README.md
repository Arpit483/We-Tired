# VitalRadar - Deep Learning Breathing Detection System
A real-time breathing detection system using CNN+LSTM deep learning models, integrated with web interface for Raspberry Pi 4.
## Features
- **Deep Learning Detection**: CNN+LSTM model for accurate breathing pattern recognition
- **Real-time Web Interface**: Flask-based dashboard with live terminal streaming
- **Sensor Integration**: LD2410 radar sensor for breathing detection
- **Zero-Latency Streaming**: Optimized architecture for instant terminal output
- **Raspberry Pi 4 Ready**: Complete deployment scripts and optimization
## Quick Start
1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the System**
   ```bash
   python3 app.py &  # Start web interface
   python3 deep_optimized.py   # Start detection system
   ```
3. **Access Dashboard**
   ```
   http://localhost:5050
   ```
## Project Structure
- `deep_optimized.py` - Main deep learning detection engine
- `app.py` - Flask web server
- `app/` - Web application components
- `cnn_lstm_fast_final_model.pt` - Trained deep learning model
- `.kiro/specs/` - Complete project specification with requirements, design, and tasks
## Deployment
See deployment guides:
- `RASPBERRY_PI_SETUP.md` - Pi 4 setup instructions
- `DEPLOY_AND_RUN.md` - Deployment procedures
- `QUICK_START.md` - Quick deployment guide
## Specification
This project follows spec-driven development with complete documentation in `.kiro/specs/deep-learning-web-integration/`:
- `requirements.md` - Detailed requirements with EARS patterns
- `design.md` - System architecture and correctness properties
- `tasks.md` - Implementation task breakdown
## License
MIT License - See LICENSE file for details
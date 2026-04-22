from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    print("[VITALRADAR] Starting Flask server with SocketIO...")
    socketio.run(app, host="0.0.0.0", port=5050, debug=False)

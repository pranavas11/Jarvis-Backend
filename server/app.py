# import eventlet
# eventlet.monkey_patch()

# import os
# from dotenv import load_dotenv
# import asyncio
# import threading
# from flask import Flask, render_template, request, jsonify
# from flask_cors import CORS
# from flask_socketio import SocketIO, emit

# load_dotenv()

# app = Flask(__name__)
# app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a_default_fallback_secret_key!')

# frontend_origin = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
# ALLOWED_ORIGINS = [frontend_origin] if frontend_origin else []

# # Enable CORS for REST endpoints
# CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# socketio = SocketIO(
#     app,
#     async_mode='eventlet',
#     cors_allowed_origins=ALLOWED_ORIGINS,
#     ping_timeout=25,
#     ping_interval=20,
#     logger=True,
#     engineio_logger=True
# )

# @app.get("/healthz")
# def health():
#     return jsonify({"ok": True}), 200

# @app.get("/")
# def root():
#     return "Jarvis backend is running! ✅", 200

# from Jarvis_Online import Jarvis

# # Use dictionary to store sessions instead of single global instance
# active_sessions = {}
# global_loop = None
# global_thread = None

# def run_asyncio_loop(loop):
#     """Function to run the asyncio event loop in a separate thread"""
#     asyncio.set_event_loop(loop)
#     try:
#         print("Global asyncio event loop started...")
#         loop.run_forever()
#     finally:
#         print("Global asyncio event loop stopping...")
#         tasks = asyncio.all_tasks(loop=loop)
#         for task in tasks:
#             if not task.done():
#                 task.cancel()
#         try:
#             loop.run_until_complete(asyncio.gather(*[t for t in tasks if not t.done()], return_exceptions=True))
#             loop.run_until_complete(loop.shutdown_asyncgens())
#         except RuntimeError as e:
#             print(f"RuntimeError during loop cleanup: {e}")
#         except Exception as e:
#             print(f"Exception during loop cleanup: {e}")
#         finally:
#             if not loop.is_closed():
#                 loop.close()
#         print("Global asyncio event loop stopped.")

# def ensure_global_loop():
#     """Ensure the global asyncio loop is running"""
#     global global_loop, global_thread
    
#     if global_thread is None or not global_thread.is_alive():
#         print("Starting global asyncio thread...")
#         global_loop = asyncio.new_event_loop()
#         global_thread = threading.Thread(target=run_asyncio_loop, args=(global_loop,), daemon=True)
#         global_thread.start()
#         socketio.sleep(0.1)  # Give thread time to start
#         print("Global asyncio thread started.")
    
#     return global_loop

# @socketio.on('connect')
# def handle_connect():
#     """Handles new client connections"""
#     client_sid = request.sid
#     print(f"\n--- handle_connect called for SID: {client_sid} ---")

#     try:
#         # Ensure global loop is running
#         loop = ensure_global_loop()
#         if not loop or not loop.is_running():
#             print(f"ERROR: Global asyncio loop not ready for SID {client_sid}")
#             emit('error', {'message': 'Server initialization error'}, room=client_sid)
#             return

#         # Check if this client already has a session (reconnection case)
#         if client_sid in active_sessions:
#             print(f"Client {client_sid} already has an active session")
#             emit('status', {'message': 'Reconnected to existing Jarvis session'}, room=client_sid)
#             return

#         # Create new Jarvis instance for this specific client
#         print(f"Creating NEW Jarvis instance for SID: {client_sid}")
#         jarvis_instance = Jarvis(socketio_instance=socketio, client_sid=client_sid)
        
#         # Store the session
#         active_sessions[client_sid] = jarvis_instance
        
#         # Start Jarvis tasks for this specific instance
#         future = asyncio.run_coroutine_threadsafe(jarvis_instance.start_all_tasks(), loop)
#         print(f"Jarvis instance created and tasks scheduled for SID: {client_sid}")
        
#         emit('status', {'message': 'Connected to Jarvis Assistant'}, room=client_sid)
#         print(f"Active sessions: {len(active_sessions)}")
        
#     except Exception as e:
#         print(f"ERROR initializing Jarvis for SID {client_sid}: {e}")
#         emit('error', {'message': f'Failed to initialize assistant: {e}'}, room=client_sid)
#         # Clean up failed session
#         if client_sid in active_sessions:
#             del active_sessions[client_sid]

#     print(f"--- handle_connect finished for SID: {client_sid} ---\n")

# @socketio.on('disconnect')
# def handle_disconnect():
#     """Handles client disconnections"""
#     client_sid = request.sid
#     print(f"\n--- handle_disconnect called for SID: {client_sid} ---")

#     if client_sid in active_sessions:
#         jarvis_instance = active_sessions[client_sid]
#         print(f"Stopping Jarvis instance for SID: {client_sid}")
        
#         if global_loop and global_loop.is_running():
#             try:
#                 future = asyncio.run_coroutine_threadsafe(jarvis_instance.stop_all_tasks(), global_loop)
#                 future.result(timeout=10)
#                 print(f"Jarvis tasks stopped for SID: {client_sid}")
#             except Exception as e:
#                 print(f"Exception stopping Jarvis tasks for SID {client_sid}: {e}")
        
#         # Remove session
#         del active_sessions[client_sid]
#         print(f"Session cleaned up for SID: {client_sid}")
#         print(f"Remaining active sessions: {len(active_sessions)}")
#     else:
#         print(f"No active session found for SID: {client_sid}")

#     print(f"--- handle_disconnect finished for SID: {client_sid} ---\n")

# @socketio.on('send_text_message')
# def handle_text_message(data):
#     """Receives text message from client's input box"""
#     client_sid = request.sid
#     message = data.get('message', '')
#     print(f"Received text from {client_sid}: {message}")
    
#     if client_sid in active_sessions:
#         jarvis_instance = active_sessions[client_sid]
#         if global_loop and global_loop.is_running():
#             asyncio.run_coroutine_threadsafe(
#                 jarvis_instance.process_input(message, is_final_turn_input=True), 
#                 global_loop
#             )
#             print(f"Text message forwarded to Jarvis for SID: {client_sid}")
#         else:
#             print(f"Cannot process text - asyncio loop not ready for SID: {client_sid}")
#             emit('error', {'message': 'Assistant busy or loop error.'}, room=client_sid)
#     else:
#         print(f"No active session for text message from SID: {client_sid}")
#         emit('error', {'message': 'Session not found. Please refresh the page.'}, room=client_sid)

# @socketio.on('send_transcribed_text')
# def handle_transcribed_text(data):
#     """Receives final transcribed text from client's Web Speech API"""
#     client_sid = request.sid
#     transcript = data.get('transcript', '')
#     print(f"Received transcript from {client_sid}: {transcript}")
    
#     if transcript and client_sid in active_sessions:
#         jarvis_instance = active_sessions[client_sid]
#         if global_loop and global_loop.is_running():
#             asyncio.run_coroutine_threadsafe(
#                 jarvis_instance.process_input(transcript, is_final_turn_input=True), 
#                 global_loop
#             )
#             print(f"Transcript forwarded to Jarvis for SID: {client_sid}")
#         else:
#             print(f"Cannot process transcript - asyncio loop not ready for SID: {client_sid}")
#             emit('error', {'message': 'Assistant busy or loop error.'}, room=client_sid)
#     elif not transcript:
#         print("Received empty transcript.")
#     else:
#         print(f"No active session for transcript from SID: {client_sid}")
#         emit('error', {'message': 'Session not found. Please refresh the page.'}, room=client_sid)

# @socketio.on('send_video_frame')
# def handle_video_frame(data):
#     """Receives base64 video frame data from client"""
#     client_sid = request.sid
#     frame_data_url = data.get('frame')

#     if frame_data_url and client_sid in active_sessions:
#         jarvis_instance = active_sessions[client_sid]
#         if global_loop and global_loop.is_running():
#             asyncio.run_coroutine_threadsafe(
#                 jarvis_instance.process_video_frame(frame_data_url), 
#                 global_loop
#             )

# @socketio.on('video_feed_stopped')
# def handle_video_feed_stopped():
#     """Client signaled that the video feed has stopped."""
#     client_sid = request.sid
#     print(f"Received video_feed_stopped signal from {client_sid}.")
    
#     if client_sid in active_sessions:
#         jarvis_instance = active_sessions[client_sid]
#         if global_loop and global_loop.is_running():
#             # Add clear_video_queue method to your Jarvis class if needed
#             if hasattr(jarvis_instance, 'clear_video_queue'):
#                 asyncio.run_coroutine_threadsafe(jarvis_instance.clear_video_queue(), global_loop)
#                 print(f"Video frame queue clearing requested for SID: {client_sid}")
#         else:
#             print(f"Cannot clear video queue - asyncio loop not ready for SID: {client_sid}")
#     else:
#         print(f"No active session for video_feed_stopped from SID: {client_sid}")

# if __name__ == '__main__':
#     print("Starting Flask-SocketIO server...")
#     try:
#         # CHANGED: Set debug=False for production
#         socketio.run(app, debug=False, host='0.0.0.0', port=5000, use_reloader=False)
#     finally:
#         print("\nServer shutting down...")
#         # Clean up all active sessions
#         for client_sid, jarvis_instance in list(active_sessions.items()):
#             print(f"Stopping Jarvis instance for SID: {client_sid}")
#             if global_loop and global_loop.is_running():
#                 try:
#                     future = asyncio.run_coroutine_threadsafe(jarvis_instance.stop_all_tasks(), global_loop)
#                     future.result(timeout=5)
#                 except Exception as e:
#                     print(f"Exception stopping Jarvis for SID {client_sid}: {e}")
        
#         active_sessions.clear()
        
#         if global_loop and global_loop.is_running():
#             print("Stopping global asyncio loop...")
#             global_loop.call_soon_threadsafe(global_loop.stop)
#             if global_thread and global_thread.is_alive():
#                 global_thread.join(timeout=5)
#         print("Shutdown complete.")












import eventlet
eventlet.monkey_patch()

import os
from dotenv import load_dotenv
import asyncio
import threading
import atexit
import signal
import sys
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a_default_fallback_secret_key!')

frontend_origin = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
ALLOWED_ORIGINS = [frontend_origin] if frontend_origin else []

# Enable CORS for REST endpoints
CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

socketio = SocketIO(
    app,
    async_mode='eventlet',
    cors_allowed_origins=ALLOWED_ORIGINS,
    ping_timeout=60,  # Increased from 25
    ping_interval=25,  # Increased from 20
    logger=False,  # Reduced logging for production
    engineio_logger=False
)

@app.get("/healthz")
def health():
    return jsonify({"ok": True}), 200

@app.get("/")
def root():
    return "Jarvis backend is running! ✅", 200

# Import after Flask app is created to avoid context issues
from Jarvis_Online import Jarvis

# Use dictionary to store sessions instead of single global instance
active_sessions = {}
global_loop = None
global_thread = None
shutdown_flag = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_flag
    print(f"Received signal {signum}. Initiating graceful shutdown...")
    shutdown_flag = True
    cleanup_all_sessions()
    sys.exit(0)

def run_asyncio_loop(loop):
    """Function to run the asyncio event loop in a separate thread"""
    asyncio.set_event_loop(loop)
    try:
        print("Global asyncio event loop started...")
        loop.run_forever()
    finally:
        print("Global asyncio event loop stopping...")
        cleanup_loop_tasks(loop)
        print("Global asyncio event loop stopped.")

def cleanup_loop_tasks(loop):
    """Clean up all tasks in the event loop"""
    try:
        tasks = asyncio.all_tasks(loop=loop)
        if tasks:
            print(f"Cancelling {len(tasks)} remaining tasks...")
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete cancellation
            try:
                loop.run_until_complete(
                    asyncio.gather(*[t for t in tasks if not t.done()], return_exceptions=True)
                )
            except Exception as e:
                print(f"Error during task cleanup: {e}")
        
        # Shutdown async generators
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception as e:
            print(f"Error shutting down async generators: {e}")
            
    except Exception as e:
        print(f"Exception during loop cleanup: {e}")
    finally:
        if not loop.is_closed():
            try:
                loop.close()
            except Exception as e:
                print(f"Error closing loop: {e}")

def ensure_global_loop():
    """Ensure the global asyncio loop is running"""
    global global_loop, global_thread
    
    if global_thread is None or not global_thread.is_alive():
        print("Starting global asyncio thread...")
        global_loop = asyncio.new_event_loop()
        global_thread = threading.Thread(target=run_asyncio_loop, args=(global_loop,), daemon=True)
        global_thread.start()
        
        # Wait for thread to start properly
        import time
        time.sleep(0.1)
        
        # Verify loop is running
        if global_loop and global_loop.is_running():
            print("Global asyncio thread started successfully.")
        else:
            print("WARNING: Global asyncio thread may not have started properly.")
    
    return global_loop

def cleanup_session(client_sid):
    """Clean up a single session"""
    if client_sid in active_sessions:
        jarvis_instance = active_sessions[client_sid]
        print(f"Cleaning up session for SID: {client_sid}")
        
        if global_loop and global_loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    jarvis_instance.stop_all_tasks(), global_loop
                )
                future.result(timeout=5)  # Reduced timeout
                print(f"Jarvis tasks stopped for SID: {client_sid}")
            except Exception as e:
                print(f"Exception stopping Jarvis tasks for SID {client_sid}: {e}")
        
        # Remove session
        del active_sessions[client_sid]
        print(f"Session cleaned up for SID: {client_sid}")

def cleanup_all_sessions():
    """Clean up all active sessions"""
    print("Cleaning up all active sessions...")
    session_ids = list(active_sessions.keys())
    
    for client_sid in session_ids:
        try:
            cleanup_session(client_sid)
        except Exception as e:
            print(f"Error cleaning up session {client_sid}: {e}")
    
    active_sessions.clear()
    print("All sessions cleaned up.")

@socketio.on('connect')
def handle_connect():
    """Handles new client connections"""
    client_sid = request.sid
    print(f"\n--- handle_connect called for SID: {client_sid} ---")

    try:
        # Check if shutting down
        if shutdown_flag:
            emit('error', {'message': 'Server is shutting down'}, room=client_sid)
            return False
            
        # Ensure global loop is running
        loop = ensure_global_loop()
        if not loop or not loop.is_running():
            print(f"ERROR: Global asyncio loop not ready for SID {client_sid}")
            emit('error', {'message': 'Server initialization error'}, room=client_sid)
            return False

        # Check if this client already has a session (reconnection case)
        if client_sid in active_sessions:
            print(f"Client {client_sid} already has an active session")
            emit('status', {'message': 'Reconnected to existing Jarvis session'}, room=client_sid)
            return True

        # Create new Jarvis instance for this specific client with app context
        print(f"Creating NEW Jarvis instance for SID: {client_sid}")
        with app.app_context():
            jarvis_instance = Jarvis(socketio_instance=socketio, client_sid=client_sid)
        
        # Store the session
        active_sessions[client_sid] = jarvis_instance
        
        # Start Jarvis tasks for this specific instance
        future = asyncio.run_coroutine_threadsafe(jarvis_instance.start_all_tasks(), loop)
        print(f"Jarvis instance created and tasks scheduled for SID: {client_sid}")
        
        emit('status', {'message': 'Connected to Jarvis Assistant'}, room=client_sid)
        print(f"Active sessions: {len(active_sessions)}")
        
    except Exception as e:
        print(f"ERROR initializing Jarvis for SID {client_sid}: {e}")
        emit('error', {'message': f'Failed to initialize assistant: {str(e)}'}, room=client_sid)
        # Clean up failed session
        if client_sid in active_sessions:
            try:
                del active_sessions[client_sid]
            except Exception:
                pass
        return False

    print(f"--- handle_connect finished for SID: {client_sid} ---\n")
    return True

@socketio.on('disconnect')
def handle_disconnect():
    """Handles client disconnections"""
    client_sid = request.sid
    print(f"\n--- handle_disconnect called for SID: {client_sid} ---")

    try:
        cleanup_session(client_sid)
        print(f"Remaining active sessions: {len(active_sessions)}")
    except Exception as e:
        print(f"Error during disconnect cleanup for SID {client_sid}: {e}")

    print(f"--- handle_disconnect finished for SID: {client_sid} ---\n")

@socketio.on('send_text_message')
def handle_text_message(data):
    """Receives text message from client's input box"""
    client_sid = request.sid
    message = data.get('message', '')
    print(f"Received text from {client_sid}: {message}")
    
    if client_sid in active_sessions:
        jarvis_instance = active_sessions[client_sid]
        if global_loop and global_loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(
                    jarvis_instance.process_input(message, is_final_turn_input=True), 
                    global_loop
                )
                print(f"Text message forwarded to Jarvis for SID: {client_sid}")
            except Exception as e:
                print(f"Error forwarding text message for SID {client_sid}: {e}")
                emit('error', {'message': 'Failed to process message'}, room=client_sid)
        else:
            print(f"Cannot process text - asyncio loop not ready for SID: {client_sid}")
            emit('error', {'message': 'Assistant busy or loop error.'}, room=client_sid)
    else:
        print(f"No active session for text message from SID: {client_sid}")
        emit('error', {'message': 'Session not found. Please refresh the page.'}, room=client_sid)

@socketio.on('send_transcribed_text')
def handle_transcribed_text(data):
    """Receives final transcribed text from client's Web Speech API"""
    client_sid = request.sid
    transcript = data.get('transcript', '')
    print(f"Received transcript from {client_sid}: {transcript}")
    
    if transcript and client_sid in active_sessions:
        jarvis_instance = active_sessions[client_sid]
        if global_loop and global_loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(
                    jarvis_instance.process_input(transcript, is_final_turn_input=True), 
                    global_loop
                )
                print(f"Transcript forwarded to Jarvis for SID: {client_sid}")
            except Exception as e:
                print(f"Error forwarding transcript for SID {client_sid}: {e}")
                emit('error', {'message': 'Failed to process transcript'}, room=client_sid)
        else:
            print(f"Cannot process transcript - asyncio loop not ready for SID: {client_sid}")
            emit('error', {'message': 'Assistant busy or loop error.'}, room=client_sid)
    elif not transcript:
        print("Received empty transcript.")
    else:
        print(f"No active session for transcript from SID: {client_sid}")
        emit('error', {'message': 'Session not found. Please refresh the page.'}, room=client_sid)

@socketio.on('send_video_frame')
def handle_video_frame(data):
    """Receives base64 video frame data from client"""
    client_sid = request.sid
    frame_data_url = data.get('frame')

    if frame_data_url and client_sid in active_sessions:
        jarvis_instance = active_sessions[client_sid]
        if global_loop and global_loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(
                    jarvis_instance.process_video_frame(frame_data_url), 
                    global_loop
                )
            except Exception as e:
                print(f"Error processing video frame for SID {client_sid}: {e}")

@socketio.on('video_feed_stopped')
def handle_video_feed_stopped():
    """Client signaled that the video feed has stopped."""
    client_sid = request.sid
    print(f"Received video_feed_stopped signal from {client_sid}.")
    
    if client_sid in active_sessions:
        jarvis_instance = active_sessions[client_sid]
        if global_loop and global_loop.is_running():
            try:
                if hasattr(jarvis_instance, 'clear_video_queue'):
                    asyncio.run_coroutine_threadsafe(jarvis_instance.clear_video_queue(), global_loop)
                    print(f"Video frame queue clearing requested for SID: {client_sid}")
            except Exception as e:
                print(f"Error clearing video queue for SID {client_sid}: {e}")
        else:
            print(f"Cannot clear video queue - asyncio loop not ready for SID: {client_sid}")
    else:
        print(f"No active session for video_feed_stopped from SID: {client_sid}")

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Register cleanup function to run at exit
atexit.register(cleanup_all_sessions)

if __name__ == '__main__':
    print("Starting Flask-SocketIO server...")
    try:
        # Use debug=False for production, avoid reloader with eventlet
        socketio.run(app, debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\nReceived KeyboardInterrupt...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        print("\nServer shutting down...")
        cleanup_all_sessions()
        
        # Stop the global loop
        if global_loop and global_loop.is_running():
            print("Stopping global asyncio loop...")
            global_loop.call_soon_threadsafe(global_loop.stop)
            
            if global_thread and global_thread.is_alive():
                global_thread.join(timeout=5)
                
        print("Shutdown complete.")
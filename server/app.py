# # app.py (Revised for Client-Side STT, CORS, Logging, AND VIDEO FRAMES)
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

# REACT_APP_PORT = os.getenv('REACT_APP_PORT', '5173')
# #REACT_APP_ORIGIN = f"http://localhost:{REACT_APP_PORT}"
# #REACT_APP_ORIGIN_IP = f"http://127.0.0.1:{REACT_APP_PORT}"

# frontend_origin = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()

# ALLOWED_ORIGINS = [frontend_origin] if frontend_origin else []

# # Enable CORS for REST endpoints too (if needed)
# CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# socketio = SocketIO(
#     app,
#     #async_mode='threading',
#     async_mode='eventlet',             # use eventlet in prod with gunicorn
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

# Jarvis_instance = None
# Jarvis_loop = None
# Jarvis_thread = None

# def run_asyncio_loop(loop):
#     """ Function to run the asyncio event loop in a separate thread """
#     asyncio.set_event_loop(loop)
#     try:
#         print("Asyncio event loop started...")
#         loop.run_forever()
#     finally:
#         print("Asyncio event loop stopping...")
#         tasks = asyncio.all_tasks(loop=loop)
#         for task in tasks:
#             if not task.done():
#                 task.cancel()
#         try:
#             loop.run_until_complete(asyncio.gather(*[t for t in tasks if not t.done()], return_exceptions=True))
#             loop.run_until_complete(loop.shutdown_asyncgens())
#         except RuntimeError as e:
#              print(f"RuntimeError during loop cleanup (might be expected if loop stopped abruptly): {e}")
#         except Exception as e:
#             print(f"Exception during loop cleanup: {e}")
#         finally:
#             if not loop.is_closed():
#                 loop.close()
#         print("Asyncio event loop stopped.")

# @socketio.on('connect')
# def handle_connect():
#     """ Handles new client connections """
#     global Jarvis_instance, Jarvis_loop, Jarvis_thread
#     client_sid = request.sid
#     print(f"\n--- handle_connect called for SID: {client_sid} ---")

#     if Jarvis_thread is None or not Jarvis_thread.is_alive():
#         print(f"    Asyncio thread not running. Starting new loop and thread.")
#         Jarvis_loop = asyncio.new_event_loop()
#         Jarvis_thread = threading.Thread(target=run_asyncio_loop, args=(Jarvis_loop,), daemon=True)
#         Jarvis_thread.start()
#         print("    Started asyncio thread.")
#         socketio.sleep(0.1)

#     if Jarvis_instance is None:
#         print(f"    Creating NEW Jarvis instance for SID: {client_sid}")
#         if not Jarvis_loop or not Jarvis_loop.is_running():
#              print(f"    ERROR: Cannot create Jarvis instance, asyncio loop not ready for SID {client_sid}.")
#              emit('error', {'message': 'Assistant initialization error (loop).'}, room=client_sid)
#              return

#         try:
#             Jarvis_instance = Jarvis(socketio_instance=socketio, client_sid=client_sid)
#             future = asyncio.run_coroutine_threadsafe(Jarvis_instance.start_all_tasks(), Jarvis_loop)
#             print("    Jarvis instance created and tasks scheduled.")
#         except ValueError as e:
#             print(f"    ERROR initializing Jarvis (ValueError) for SID {client_sid}: {e}")
#             emit('error', {'message': f'Failed to initialize assistant: {e}'}, room=client_sid)
#             Jarvis_instance = None
#             return
#         except Exception as e:
#             print(f"    ERROR initializing Jarvis (Unexpected) for SID {client_sid}: {e}")
#             emit('error', {'message': f'Unexpected error initializing assistant: {e}'}, room=client_sid)
#             Jarvis_instance = None
#             return
#     else:
#         print(f"    Jarvis instance already exists. Updating SID from {Jarvis_instance.client_sid} to {client_sid}")
#         Jarvis_instance.client_sid = client_sid

#     if Jarvis_instance:
#         emit('status', {'message': 'Connected to Jarvis Assistant'}, room=client_sid)
#     print(f"--- handle_connect finished for SID: {client_sid} ---\n")


# @socketio.on('disconnect')
# def handle_disconnect():
#     """ Handles client disconnections """
#     global Jarvis_instance
#     client_sid = request.sid
#     print(f"\n--- handle_disconnect called for SID: {client_sid} ---")

#     if Jarvis_instance and Jarvis_instance.client_sid == client_sid:
#         print(f"    Designated client {client_sid} disconnected. Attempting to stop Jarvis.")
#         if Jarvis_loop and Jarvis_loop.is_running():
#             future = asyncio.run_coroutine_threadsafe(Jarvis_instance.stop_all_tasks(), Jarvis_loop)
#             try:
#                 future.result(timeout=10)
#                 print("    Jarvis tasks stopped successfully.")
#             except TimeoutError:
#                 print("    Timeout waiting for Jarvis tasks to stop.")
#             except Exception as e:
#                 print(f"    Exception during Jarvis task stop: {e}")
#             finally:
#                  pass # Keep loop running

#         else:
#              print(f"    Cannot stop Jarvis tasks: asyncio loop not available or not running.")

#         Jarvis_instance = None
#         print("    Jarvis instance cleared.")

#     elif Jarvis_instance:
#          print(f"    Disconnecting client {client_sid} is NOT the designated client ({Jarvis_instance.client_sid}). Jarvis remains active.")
#     else:
#          print(f"    Client {client_sid} disconnected, but no active Jarvis instance found.")

#     print(f"--- handle_disconnect finished for SID: {client_sid} ---\n")


# @socketio.on('send_text_message')
# def handle_text_message(data):
#     """ Receives text message from client's input box """
#     client_sid = request.sid
#     message = data.get('message', '')
#     print(f"Received text from {client_sid}: {message}")
#     if Jarvis_instance and Jarvis_instance.client_sid == client_sid:
#         if Jarvis_loop and Jarvis_loop.is_running():
#             # Process text with end_of_turn=True implicitly handled in process_input -> run_gemini_session
#             asyncio.run_coroutine_threadsafe(Jarvis_instance.process_input(message, is_final_turn_input=True), Jarvis_loop)
#             print(f"    Text message forwarded to Jarvis for SID: {client_sid}")
#         else:
#             print(f"    Cannot process text message for SID {client_sid}: asyncio loop not ready.")
#             emit('error', {'message': 'Assistant busy or loop error.'}, room=client_sid)
#     else:
#         print(f"    Jarvis instance not ready or SID mismatch for text message from {client_sid}.")
#         emit('error', {'message': 'Assistant not ready or session mismatch.'}, room=client_sid)

# @socketio.on('send_transcribed_text')
# def handle_transcribed_text(data):
#     """ Receives final transcribed text from client's Web Speech API """
#     client_sid = request.sid
#     transcript = data.get('transcript', '')
#     print(f"Received transcript from {client_sid}: {transcript}")
#     if transcript and Jarvis_instance and Jarvis_instance.client_sid == client_sid:
#          if Jarvis_loop and Jarvis_loop.is_running():
#             # Process transcript with end_of_turn=True implicitly handled in process_input -> run_gemini_session
#             asyncio.run_coroutine_threadsafe(Jarvis_instance.process_input(transcript, is_final_turn_input=True), Jarvis_loop)
#             print(f"    Transcript forwarded to Jarvis for SID: {client_sid}")
#          else:
#              print(f"    Cannot process transcript for SID {client_sid}: asyncio loop not ready.")
#              emit('error', {'message': 'Assistant busy or loop error.'}, room=client_sid)
#     elif not transcript:
#          print("    Received empty transcript.")
#     else:
#          print(f"    Jarvis instance not ready or SID mismatch for transcript from {client_sid}.")

# # **** ADD VIDEO FRAME HANDLER ****
# @socketio.on('send_video_frame')
# def handle_video_frame(data):
#     """ Receives base64 video frame data from client """
#     client_sid = request.sid
#     frame_data_url = data.get('frame') # Expecting data URL like 'data:image/jpeg;base64,xxxxx'

#     if frame_data_url and Jarvis_instance and Jarvis_instance.client_sid == client_sid:
#         if Jarvis_loop and Jarvis_loop.is_running():
#             print(f"Received video frame from {client_sid}, forwarding...") # Optional: very verbose
#             asyncio.run_coroutine_threadsafe(Jarvis_instance.process_video_frame(frame_data_url), Jarvis_loop)
#         pass

# @socketio.on('video_feed_stopped')
# def handle_video_feed_stopped():
#     """ Client signaled that the video feed has stopped. """
#     client_sid = request.sid
#     print(f"Received video_feed_stopped signal from {client_sid}.")
#     if Jarvis_instance and Jarvis_instance.client_sid == client_sid:
#         if Jarvis_loop and Jarvis_loop.is_running():
#             # Call a method on Jarvis instance to clear its video queue
#             asyncio.run_coroutine_threadsafe(Jarvis_instance.clear_video_queue(), Jarvis_loop)
#             print(f"    Video frame queue clearing requested for SID: {client_sid}")
#         else:
#             print(f"    Cannot clear video queue for SID {client_sid}: asyncio loop not ready.")
#     else:
#         print(f"    Jarvis instance not ready or SID mismatch for video_feed_stopped from {client_sid}.")


# if __name__ == '__main__':
#     print("Starting Flask-SocketIO server...")
#     try:
#         socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False)
#     finally:
#         print("\nServer shutting down...")
#         if Jarvis_instance:
#              print("Attempting to stop active Jarvis instance on server shutdown...")
#              if Jarvis_loop and Jarvis_loop.is_running():
#                  future = asyncio.run_coroutine_threadsafe(Jarvis_instance.stop_all_tasks(), Jarvis_loop)
#                  try:
#                      future.result(timeout=5)
#                      print("Jarvis tasks stopped.")
#                  except TimeoutError:
#                      print("Timeout stopping Jarvis tasks during shutdown.")
#                  except Exception as e:
#                      print(f"Exception stopping Jarvis tasks during shutdown: {e}")
#              else:
#                  print("Cannot stop Jarvis instance: asyncio loop not available.")
#              Jarvis_instance = None

#         if Jarvis_loop and Jarvis_loop.is_running():
#              print("Stopping asyncio loop from main thread...")
#              Jarvis_loop.call_soon_threadsafe(Jarvis_loop.stop)
#              if Jarvis_thread and Jarvis_thread.is_alive():
#                  Jarvis_thread.join(timeout=5)
#                  if Jarvis_thread.is_alive():
#                      print("Warning: Asyncio thread did not exit cleanly.")
#              print("Asyncio loop/thread stop initiated.")
#         print("Shutdown complete.")

















# app.py (Corrected for Multi-Session Support)
import eventlet
eventlet.monkey_patch()

import os
from dotenv import load_dotenv
import asyncio
import threading
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
    ping_timeout=25,
    ping_interval=20,
    logger=True,
    engineio_logger=True
)

@app.get("/healthz")
def health():
    return jsonify({"ok": True}), 200

@app.get("/")
def root():
    return "Jarvis backend is running! ✅", 200

from Jarvis_Online import Jarvis

# CHANGED: Use dictionary to store sessions instead of single global instance
active_sessions = {}  # {client_sid: jarvis_instance}
global_loop = None
global_thread = None

def run_asyncio_loop(loop):
    """Function to run the asyncio event loop in a separate thread"""
    asyncio.set_event_loop(loop)
    try:
        print("Global asyncio event loop started...")
        loop.run_forever()
    finally:
        print("Global asyncio event loop stopping...")
        tasks = asyncio.all_tasks(loop=loop)
        for task in tasks:
            if not task.done():
                task.cancel()
        try:
            loop.run_until_complete(asyncio.gather(*[t for t in tasks if not t.done()], return_exceptions=True))
            loop.run_until_complete(loop.shutdown_asyncgens())
        except RuntimeError as e:
            print(f"RuntimeError during loop cleanup: {e}")
        except Exception as e:
            print(f"Exception during loop cleanup: {e}")
        finally:
            if not loop.is_closed():
                loop.close()
        print("Global asyncio event loop stopped.")

def ensure_global_loop():
    """Ensure the global asyncio loop is running"""
    global global_loop, global_thread
    
    if global_thread is None or not global_thread.is_alive():
        print("Starting global asyncio thread...")
        global_loop = asyncio.new_event_loop()
        global_thread = threading.Thread(target=run_asyncio_loop, args=(global_loop,), daemon=True)
        global_thread.start()
        socketio.sleep(0.1)  # Give thread time to start
        print("Global asyncio thread started.")
    
    return global_loop

@socketio.on('connect')
def handle_connect():
    """Handles new client connections"""
    client_sid = request.sid
    print(f"\n--- handle_connect called for SID: {client_sid} ---")

    try:
        # Ensure global loop is running
        loop = ensure_global_loop()
        if not loop or not loop.is_running():
            print(f"ERROR: Global asyncio loop not ready for SID {client_sid}")
            emit('error', {'message': 'Server initialization error'}, room=client_sid)
            return

        # Check if this client already has a session (reconnection case)
        if client_sid in active_sessions:
            print(f"Client {client_sid} already has an active session")
            emit('status', {'message': 'Reconnected to existing Jarvis session'}, room=client_sid)
            return

        # Create new Jarvis instance for this specific client
        print(f"Creating NEW Jarvis instance for SID: {client_sid}")
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
        emit('error', {'message': f'Failed to initialize assistant: {e}'}, room=client_sid)
        # Clean up failed session
        if client_sid in active_sessions:
            del active_sessions[client_sid]

    print(f"--- handle_connect finished for SID: {client_sid} ---\n")

@socketio.on('disconnect')
def handle_disconnect():
    """Handles client disconnections"""
    client_sid = request.sid
    print(f"\n--- handle_disconnect called for SID: {client_sid} ---")

    if client_sid in active_sessions:
        jarvis_instance = active_sessions[client_sid]
        print(f"Stopping Jarvis instance for SID: {client_sid}")
        
        if global_loop and global_loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(jarvis_instance.stop_all_tasks(), global_loop)
                future.result(timeout=10)
                print(f"Jarvis tasks stopped for SID: {client_sid}")
            except Exception as e:
                print(f"Exception stopping Jarvis tasks for SID {client_sid}: {e}")
        
        # Remove session
        del active_sessions[client_sid]
        print(f"Session cleaned up for SID: {client_sid}")
        print(f"Remaining active sessions: {len(active_sessions)}")
    else:
        print(f"No active session found for SID: {client_sid}")

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
            asyncio.run_coroutine_threadsafe(
                jarvis_instance.process_input(message, is_final_turn_input=True), 
                global_loop
            )
            print(f"Text message forwarded to Jarvis for SID: {client_sid}")
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
            asyncio.run_coroutine_threadsafe(
                jarvis_instance.process_input(transcript, is_final_turn_input=True), 
                global_loop
            )
            print(f"Transcript forwarded to Jarvis for SID: {client_sid}")
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
            asyncio.run_coroutine_threadsafe(
                jarvis_instance.process_video_frame(frame_data_url), 
                global_loop
            )

@socketio.on('video_feed_stopped')
def handle_video_feed_stopped():
    """Client signaled that the video feed has stopped."""
    client_sid = request.sid
    print(f"Received video_feed_stopped signal from {client_sid}.")
    
    if client_sid in active_sessions:
        jarvis_instance = active_sessions[client_sid]
        if global_loop and global_loop.is_running():
            # Add clear_video_queue method to your Jarvis class if needed
            if hasattr(jarvis_instance, 'clear_video_queue'):
                asyncio.run_coroutine_threadsafe(jarvis_instance.clear_video_queue(), global_loop)
                print(f"Video frame queue clearing requested for SID: {client_sid}")
        else:
            print(f"Cannot clear video queue - asyncio loop not ready for SID: {client_sid}")
    else:
        print(f"No active session for video_feed_stopped from SID: {client_sid}")

if __name__ == '__main__':
    print("Starting Flask-SocketIO server...")
    try:
        # CHANGED: Set debug=False for production
        socketio.run(app, debug=False, host='0.0.0.0', port=5000, use_reloader=False)
    finally:
        print("\nServer shutting down...")
        # Clean up all active sessions
        for client_sid, jarvis_instance in list(active_sessions.items()):
            print(f"Stopping Jarvis instance for SID: {client_sid}")
            if global_loop and global_loop.is_running():
                try:
                    future = asyncio.run_coroutine_threadsafe(jarvis_instance.stop_all_tasks(), global_loop)
                    future.result(timeout=5)
                except Exception as e:
                    print(f"Exception stopping Jarvis for SID {client_sid}: {e}")
        
        active_sessions.clear()
        
        if global_loop and global_loop.is_running():
            print("Stopping global asyncio loop...")
            global_loop.call_soon_threadsafe(global_loop.stop)
            if global_thread and global_thread.is_alive():
                global_thread.join(timeout=5)
        print("Shutdown complete.")
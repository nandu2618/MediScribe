import pyaudio
import threading
import queue
import speech_recognition as sr
import time
import socketio
from io import BytesIO
from primary_model import process_text  # Ensure this function is accessible from primary_model

# Socket.io client setup
sio = socketio.Client()

# Queue to hold audio chunks for processing
audio_queue = queue.Queue()

# Function to record continuously in chunks (capturing from WebRTC audio input)
def continuous_audio_stream(duration_per_chunk=10):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        while True:
            print("Listening for audio chunk...")
            recognizer.adjust_for_ambient_noise(source)
            try:
                # Adjust the timeout duration or handle it gracefully
                audio = recognizer.listen(source, timeout=5)  # Adjust timeout as necessary
                print("Audio captured successfully")
                # Place the captured audio into the queue for processing
                audio_queue.put(audio)  # Add captured audio to the queue
            except sr.WaitTimeoutError:
                print("Listening timed out. Retrying...")
                continue  # Continue listening after timeout
            except Exception as e:
                print(f"Error in audio capture: {e}")

# Example of emitting the prescription to the front-end (Patient) after processing speech
def process_audio_chunk():
    while True:
        if not audio_queue.empty():
            audio = audio_queue.get()  # Retrieve audio from the queue
            print("Processing audio chunk...")

            try:
                # Recognize audio and convert it to text
                transcribed_text = sr.Recognizer().recognize_google(audio)
                print(f"Transcribed Text: {transcribed_text}")

                # Send transcribed text to primary model for processing
                result = process_text(transcribed_text)  # Ensure this is a function that returns results from the primary model
                print(f"Processed Result: {result}")

                # Send the processed result (e.g., prescription) via socket to the front-end (patient)
                sio.emit('endCall', {'prescription': result['prescription']})  # Emit result to the patient

            except Exception as e:
                print(f"Error in audio recognition: {e}")


# Function to transcribe audio from WebRTC
def transcribe_audio(audio_bytes):
    recognizer = sr.Recognizer()
    audio_data = sr.AudioData(audio_bytes, 16000, 2)  # Assuming 16kHz, 2 channels for WebRTC audio
    try:
        transcribed_text = recognizer.recognize_google(audio_data)
        print(f"Transcribed Text: {transcribed_text}")
        return transcribed_text
    except Exception as e:
        print(f"Error in audio transcription: {e}")
        return None

# Function to receive audio data from WebRTC (sent from the front-end)
@sio.event
def audio_data(data):
    audio_bytes = BytesIO(data)  # Convert the byte data from WebRTC into a byte stream
    print("Received audio data from WebRTC")

    # Transcribe the audio data
    transcribed_text = transcribe_audio(audio_bytes)
    if transcribed_text:
        print(f"Transcribed Text: {transcribed_text}")
        
        # Send the transcribed text to the primary model for processing
        result = process_text(transcribed_text)
        print(f"Processed Result: {result}")
        
        # After processing the transcribed text and generating a prescription:
        print(f"Generated Prescription: {result}")
        sio.emit('prescription', {'prescription': result})  # result should be the actual prescription text


    else:
        print("Error in transcription")

@sio.event
def connect():
    print("Connected to server!")

@sio.event
def connect_error(data):
    print(f"Connection failed: {data}")

@sio.event
def disconnect():
    print("Disconnected from server")

# Function to connect to the server
def connect_to_server():
    try:
        if sio.connected:
            sio.disconnect()  # Disconnect the client if already connected

        sio.connect('https://3ee8-115-99-153-90.ngrok-free.app')  # Replace with your actual server URL
        print("Connected to the server successfully.")

    except Exception as e:
        print(f"Error connecting to server: {e}")

# Connect to the WebSocket server
connect_to_server()

# Start the audio recording thread (continuously capture audio from mic)
audio_thread = threading.Thread(target=continuous_audio_stream)
audio_thread.start()

# Start the text processing thread
processing_thread = threading.Thread(target=process_audio_chunk)
processing_thread.start()

# Keep the main thread running while background threads process audio
while True:
    time.sleep(1)

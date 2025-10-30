import cv2
import time
import datetime
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os # For directory creation and path manipulation
import threading # For non-blocking email sending

# --- Email Function ---
def send_email(image_path, location="Front Entrance"):
    """
    Sends an email with a detected person image as an attachment.
    This function is designed to be called in a separate thread to prevent GUI freezing.
    
    Args:
        image_path (str): The path to the image file to attach.
        location (str): The location where the detection occurred (e.g., "Front Entrance").
    """
    try:
        msg = EmailMessage()
        
        # Get the current exact time and date for the email body
        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Construct the email body as per the requested format
        full_body = f"""Hello,

This is an automated alert from the SMART EYE system.
A person has been detected.
Time: {current_timestamp}
Location: {location}

Please find the attached image for more details.

Regards,
SMART EYE System
"""
        
        msg.set_content(full_body)
        msg['Subject'] = "SMART EYE Alert: Person Detected!" # Consistent subject line
        msg['From'] = 'pfinal480@gmail.com' # <<< IMPORTANT: Replace with your actual sender email >>>
        msg['To'] = 'shreyachakrasali16@gmail.com' # <<< IMPORTANT: Replace with your actual recipient email >>>

        # Read the image and attach it to the email
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
        msg.add_attachment(img_data, maintype='image', subtype='jpeg', filename='person_detection.jpg')

        email_user = 'pfinal480@gmail.com' # <<< IMPORTANT: Your sender email again >>>
        # IMPORTANT: Replace with your generated Gmail App Password
        email_password = 'tydn hwwc qwzt xyzo' # <<< IMPORTANT: Replace with your generated App Password >>>

        # Using SMTP and starting TLS for security on Gmail's server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() # Upgrade the connection to a secure encrypted SSL/TLS connection
        server.login(email_user, email_password) # Log in to the SMTP server

        server.send_message(msg) # Send the email
        print(f"E-mail sent successfully from {email_user} to {msg['To']}!")
        server.quit() # Close the connection to the SMTP server
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        # Display an error message in a Tkinter messagebox if possible
        try:
            # Using a lambda to defer the messagebox call to the main thread,
            # as Tkinter operations should ideally happen there.
            root.after(0, lambda: messagebox.showerror("Email Error", f"Failed to send email: {e}\n"
                                                                         "Please check your email credentials (especially the App Password) "
                                                                         "and internet connection. Also ensure an internet connection."))
        except Exception as mb_e:
            print(f"Could not display messagebox for email error (Tkinter root might be unavailable): {mb_e}")
        return False

# --- Smart Eye Application Class ---
class SmartEyeApp:
    """
    Main application class for the Smart Eye security system with a Tkinter GUI.
    Handles camera feed, person detection, video recording, and email alerts.
    """
    def __init__(self, master):
        self.master = master
        master.title("Smart Eye Security System")
        master.geometry("800x600") # Set initial window size
        master.resizable(True, True) # Allow window resizing
        master.protocol("WM_DELETE_WINDOW", self.on_closing) # Handle window close event gracefully

        self.cap = None # OpenCV video capture object
        # Load the pre-trained Haar Cascade classifier for full-body detection
        self.body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')
        
        # --- Check if cascade loaded successfully ---
        if self.body_cascade.empty():
            messagebox.showerror("Haar Cascade Error", "Could not load haarcascade_fullbody.xml. \n"
                                                      "Ensure OpenCV is correctly installed and its data files are accessible.")
            self.master.destroy() # Exit the application if classifier cannot be loaded

        # --- Detection and Recording State Variables ---
        self.detection = False # Flag: True if a person is currently detected AND recording is active
        self.detection_stopped_time = None # Timestamp when detection last stopped
        self.timer_started = False # Flag: True if the 10-second recording buffer timer is active
        self.SECONDS_TO_RECORD_AFTER_DETECTION = 10 # Record for this many seconds AFTER last detection
        self.out = None # OpenCV VideoWriter object for saving video
        self.video_filename = "" # Stores the full path of the current video file being recorded

        # Initialize GUI elements
        self.create_widgets()

    def create_widgets(self):
        """
        Creates and arranges all the Tkinter widgets for the GUI.
        """
        # Frame to hold the camera feed canvas
        self.video_frame = ttk.Frame(self.master, borderwidth=2, relief="groove")
        self.video_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Canvas to display the camera feed
        self.canvas = tk.Canvas(self.video_frame, bg="black")
        self.canvas.pack(fill="both", expand=True) # Canvas fills the video_frame

        # Status label to show current application status
        self.status_label = ttk.Label(self.master, text="Status: Ready", font=("Arial", 12))
        self.status_label.pack(pady=5)

        # Frame to hold control buttons
        self.button_frame = ttk.Frame(self.master)
        self.button_frame.pack(pady=10)

        # Start Camera button
        self.start_button = ttk.Button(self.button_frame, text="Start Camera", command=self.start_camera)
        self.start_button.grid(row=0, column=0, padx=10, ipadx=10, ipady=5)

        # Stop Camera button (initially disabled)
        self.stop_button = ttk.Button(self.button_frame, text="Stop Camera", command=self.stop_camera, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=10, ipadx=10, ipady=5)

    def start_camera(self):
        """
        Initializes the webcam and starts the video feed update loop.
        """
        self.cap = cv2.VideoCapture(0) # Open the default webcam (index 0)
        if not self.cap.isOpened():
            messagebox.showerror("Camera Error", "Could not open video stream. \n"
                                                 "Please ensure your webcam is connected, not in use by another application, \n"
                                                 "and drivers are installed correctly.")
            self.status_label.config(text="Status: Error opening camera")
            return

        self.start_button.config(state=tk.DISABLED) # Disable start button
        self.stop_button.config(state=tk.NORMAL)   # Enable stop button
        self.status_label.config(text="Status: Camera ON, monitoring for persons...")
        
        # Get actual frame size from the camera
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.frame_size = (self.frame_width, self.frame_height)
        self.fourcc = cv2.VideoWriter_fourcc(*"mp4v") # Codec for MP4 video (compatible with many players)

        self.update_frame() # Start the continuous frame update loop

    def stop_camera(self):
        """
        Releases camera resources and stops video recording if active.
        """
        if self.cap and self.cap.isOpened():
            self.cap.release() # Release the webcam
            self.cap = None
            if self.out: # If recording is active, release the video writer
                self.out.release()
                print(f"Finished recording: {self.video_filename}")
                self.out = None
                self.video_filename = "" # Clear filename once recording is done
            self.canvas.delete("all") # Clear the canvas display
            self.status_label.config(text="Status: Camera OFF")
            self.start_button.config(state=tk.NORMAL) # Enable start button
            self.stop_button.config(state=tk.DISABLED)  # Disable stop button
            print("Camera stopped and resources released.")
            # Reset all detection-related flags to initial state
            self.detection = False
            self.timer_started = False
            self.detection_stopped_time = None

    def update_frame(self):
        """
        Reads a frame from the webcam, performs person detection,
        updates the GUI, and handles video recording/email alerts.
        This method calls itself repeatedly using after() to create the live feed.
        """
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                print("Error: Failed to read frame from webcam. Stopping camera.")
                self.stop_camera() # Stop if frame read fails
                return

            # Convert frame to grayscale for faster processing by Haar Cascades
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect persons in the grayscale frame using the full body cascade
            # Parameters for detectMultiScale are tuned for general full-body detection:
            #   scaleFactor: How much the image size is reduced at each image scale (1.05 = 5% reduction, more accurate but slower)
            #   minNeighbors: How many neighbors each candidate rectangle should have to retain it (higher = fewer but higher quality detections)
            #   minSize: Minimum possible object size. Objects smaller than this are ignored.
            persons = self.body_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=5, minSize=(50, 100)) 

            # --- Logic for recording and email alerts ---
            if len(persons) > 0: # If persons are detected in the current frame
                if not self.detection: # This block runs ONLY on the FIRST detection of a NEW event
                    print("DEBUG: New person detected. Starting recording and email.")
                    self.detection = True # Set detection flag to True, indicating recording should start/continue
                    self.timer_started = False # Reset timer, as a person is now actively detected
                    self.detection_stopped_time = None # Clear stop timer timestamp

                    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    
                    # Ensure 'recordings' directory exists
                    recordings_dir = "recordings"
                    if not os.path.exists(recordings_dir):
                        try:
                            os.makedirs(recordings_dir)
                            print(f"Created directory: {recordings_dir}")
                        except OSError as e:
                            print(f"Error creating recordings directory '{recordings_dir}': {e}")
                            messagebox.showerror("File System Error", f"Could not create '{recordings_dir}' directory: {e}")
                            self.stop_camera() # Stop if cannot write files
                            return

                    # Initialize VideoWriter to save video - Starts recording
                    self.video_filename = os.path.join(recordings_dir, f"{current_time_str}.mp4")
                    try:
                        self.out = cv2.VideoWriter(self.video_filename, self.fourcc, 20.0, self.frame_size)
                        print(f"Started recording to {self.video_filename}!")
                        self.status_label.config(text=f"Status: PERSON DETECTED! Recording to {os.path.basename(self.video_filename)}")
                    except Exception as e:
                        print(f"Error initializing video writer: {e}")
                        messagebox.showerror("Recording Error", f"Could not start video recording: {e}")
                        self.stop_camera()
                        return

                    # Save the current frame as an image and send email (simultaneously with recording start)
                    image_filename = os.path.join(recordings_dir, f"{current_time_str}.jpg")
                    try:
                        cv2.imwrite(image_filename, frame) # Save the frame with detected persons
                        print(f"Snapshot saved: {image_filename}")
                        # Call send_email in a separate thread to avoid blocking the GUI
                        email_thread = threading.Thread(target=send_email, args=(image_filename, "Front Entrance"))
                        email_thread.start()
                        print("Email sending initiated in background.")
                    except Exception as e:
                        print(f"Error saving snapshot or initiating email: {e}")
                        messagebox.showwarning("Action Warning", f"Could not save snapshot or send email: {e}")

                else:
                    # If persons are continuously present (detection is True), ensure the stop timer is reset.
                    # This prevents recording from stopping while people are still in view.
                    if self.timer_started: 
                        print("DEBUG: Person still detected. Resetting stop timer.")
                        self.timer_started = False 
                        self.detection_stopped_time = None # Clear the time to indicate no active stop timer
            
            elif self.detection: # No persons detected (len(persons) is 0), AND we were previously detecting
                # This block handles starting and managing the recording buffer before stopping.
                if not self.timer_started: # If the buffer timer hasn't started yet
                    print(f"DEBUG: No persons detected, starting {self.SECONDS_TO_RECORD_AFTER_DETECTION}s recording buffer...")
                    self.timer_started = True
                    self.detection_stopped_time = time.time() # Record the time detection stopped
                elif time.time() - self.detection_stopped_time >= self.SECONDS_TO_RECORD_AFTER_DETECTION:
                    # If the timer has expired, stop recording and reset state
                    print("DEBUG: Stop timer expired. Stopping recording and resetting detection state.")
                    if self.out:
                        self.out.release() # Release the video writer
                        print(f"Stopped recording: {self.video_filename}")
                        self.out = None
                        self.video_filename = "" # Clear filename
                    self.detection = False # Reset detection flag to False
                    self.timer_started = False 
                    self.detection_stopped_time = None # Clear the timer timestamp
                    self.status_label.config(text="Status: Camera ON, monitoring for persons...")
                    print("Transitioned back to monitoring mode (recording stopped).")
            else: # No persons detected, AND self.detection is already False (system is in monitoring state)
                pass # No specific action needed, just keep processing frames and monitoring

            # --- Visual Indicators on Frame ---
            # Display current system status text on the live video feed
            if self.detection:
                status_text = "STATUS: PERSON DETECTED & RECORDING"
                status_color = (0, 0, 255) # Red for active detection/recording
            else:
                status_text = "STATUS: MONITORING"
                status_color = (255, 255, 0) # Yellow for idle monitoring
            
            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
            
            # Display current recording filename if recording is active
            if self.out and self.video_filename:
                cv2.putText(frame, f"Recording: {os.path.basename(self.video_filename)}", (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2) # Cyan text

            # --- Write the current frame to the video file ---
            # This happens continuously if a person is detected (self.detection is True) and the recorder is initialized.
            if self.detection and self.out:
                self.out.write(frame)

            # --- Display the frame in Tkinter GUI ---
            # Convert OpenCV BGR image to RGB for Pillow/Tkinter
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img) # Create a Pillow Image from the array

            # Resize image to fit canvas while maintaining aspect ratio
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width > 0 and canvas_height > 0:
                img_aspect = img.width / img.height
                canvas_aspect = canvas_width / canvas_height

                if img_aspect > canvas_aspect: # Image is wider than canvas
                    new_width = canvas_width
                    new_height = int(new_width / img_aspect)
                else: # Image is taller or aspect ratio is the same
                    new_height = canvas_height
                    new_width = int(new_height * img_aspect)
                
                # Ensure dimensions are at least 1x1 to prevent errors with very small windows
                new_width = max(1, new_width)
                new_height = max(1, new_height)

                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS) # High quality resize

            img_tk = ImageTk.PhotoImage(image=img) # Convert Pillow Image to Tkinter PhotoImage

            # Update the canvas with the new frame
            self.canvas.delete("all") # Clear previous images on the canvas before drawing new one
            self.canvas.create_image(canvas_width / 2, canvas_height / 2, anchor=tk.CENTER, image=img_tk)
            self.canvas.image = img_tk # Important: Keep a reference to prevent garbage collection

        # Schedule the next frame update after 10 milliseconds (approx. 100 FPS refresh rate for GUI)
        self.master.after(10, self.update_frame)

    def on_closing(self):
        """
        Handles the window closing event, prompting the user before quitting
        and ensuring resources are properly released.
        """
        if messagebox.askokcancel("Quit Smart Eye", "Are you sure you want to quit Smart Eye?"):
            self.stop_camera() # Ensure camera and video writer are released cleanly
            self.master.destroy() # Destroy the Tkinter window

# --- Main Application Run ---
if __name__ == "__main__":
    root = tk.Tk() # Create the main Tkinter window
    app = SmartEyeApp(root) # Create an instance of the SmartEyeApp
    root.mainloop() # Start the Tkinter event loop (this keeps the GUI running)
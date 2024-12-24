const express = require('express');
const http = require('http');
const socketIO = require('socket.io');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = require('socket.io')(server, {
  cors: {
    origin: "https://3ee8-115-99-153-90.ngrok-free.app", // Adjust this URL as needed
    methods: ["GET", "POST"]
  }
});

// Static files for the app
app.use(express.static(path.join(__dirname)));

// Serve HTML pages for roles
app.get('/mediscribe', (req, res) => {
  res.sendFile(path.join(__dirname, 'Main_page.html'));
});
app.get('/doc', (req, res) => {
  res.sendFile(path.join(__dirname, 'Doctor.html'));
});
app.get('/pat', (req, res) => {
  res.sendFile(path.join(__dirname, 'Patient.html'));
});
app.get('/favicon.ico', (req, res) => {
  res.sendFile(path.join(__dirname, 'Resources', 'favicon.ico'));
});

// Socket.IO for real-time interaction
io.on('connection', (socket) => {
  console.log('User connected');
  
  socket.on('endCall', (data) => {
    // Emit the prescription received from the secondary model to the patient
    socket.broadcast.emit('endCall', { prescription: data.prescription });
  });


  socket.on('offer', (offer) => socket.broadcast.emit('offer', offer));
  socket.on('answer', (answer) => socket.broadcast.emit('answer', answer));
  socket.on('candidate', (candidate) => socket.broadcast.emit('candidate', candidate));
  socket.on('audioData', (data) => {
    console.log('Received audio data from front-end');
    socket.emit('prescription', { prescription: 'Generated prescription based on transcribed text' });
  });
  socket.on('disconnect', () => console.log('User disconnected'));
});

// Start server
server.listen(3000, () => {
  console.log('Server is running on port 3000');
});

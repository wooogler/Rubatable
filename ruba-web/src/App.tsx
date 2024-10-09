import { useState } from "react";
import io from "socket.io-client";
import "./App.css";

const socket = io("http://localhost:5000");

function App() {
  const [status, setStatus] = useState("");

  const sendControlCommand = (command: string) => {
    socket.emit("control", command);
  };

  socket.on("response", (data) => {
    setStatus(`Action: ${data.action}, Status: ${data.status}`);
  });

  return (
    <div className="App">
      <header className="App-header">
        <h1>Sit-Stand Desk Controller</h1>
        <button onClick={() => sendControlCommand("UP")}>Move Up</button>
        <button onClick={() => sendControlCommand("DOWN")}>Move Down</button>
        <div className="status">
          <p>{status}</p>
        </div>
      </header>
    </div>
  );
}

export default App;

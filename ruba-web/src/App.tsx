import { useState, useEffect } from "react";
import io from "socket.io-client";
import "./App.css";

const socket = io("http://localhost:5000", {
  transports: ["websocket"],
  extraHeaders: {
    "Access-Control-Allow-Origin": "http://localhost:5173",
  },
});

function App() {
  const [status, setStatus] = useState("");
  const [height, setHeight] = useState<number | null>(null);

  useEffect(() => {
    socket.on("response", (data) => {
      setStatus(`Action: ${data.action}, Result: ${data.result}`);
      if (data.height) {
        setHeight(data.height);
      }
    });

    socket.on("height_update", (data) => {
      setHeight(data.height);
    });

    return () => {
      socket.off("response");
      socket.off("height_update");
    };
  }, []);

  const sendControlCommand = (command: string) => {
    socket.emit("control", command);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Sit-Stand Desk Controller</h1>
        <button onClick={() => sendControlCommand("UP")}>Move Up</button>
        <button onClick={() => sendControlCommand("DOWN")}>Move Down</button>
        <button onClick={() => sendControlCommand("STOP")}>Stop</button>
        <div className="status">
          <p>{status}</p>
          {height !== null && <p>Current Height: {height} cm</p>}
        </div>
      </header>
    </div>
  );
}

export default App;

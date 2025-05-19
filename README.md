


# Trade Simulator

A real-time trade simulation tool that connects to the **OKX L2 order book feed** and provides live market data analysis.
 ![Trade Dashboard](https://github.com/rivshr27/Library-Management-System-rivshr/blob/main/deploy-images/Screenshot%202024-08-16%20at%206.24.28%E2%80%AFPM.png)
---

## Prerequisites

Before running the application, ensure you have the following:

- **Python 3.7+** installed  
  Download from [python.org](https://www.python.org/downloads/)  
- **pip** (comes bundled with Python)  
- **Web Browser:** Chrome, Firefox, Edge, or Safari  
- **Text Editor:** VS Code, Sublime Text, Notepad++, or any preferred editor  
- **VPN:** May be required to access OKX depending on your geographic location  

---

## Installation Steps

### 1. Create Project Folder

Open your terminal or command prompt and run:


mkdir MyTradeSimulator
cd MyTradeSimulator


### 2. Install Required Python Libraries

Within your project folder, install dependencies using:


pip install websockets numpy


### 3. Save Code Files

* Save your **backend Python script** as `trade_backend.py`
* Save your **frontend HTML file** as `trade_frontend.html`

---

## Running the Application

### Step 1: Start the Python Backend Server

Run this command inside the project directory:

```bash
python trade_backend.py
```

You should see log output like:

```
INFO:root:Starting Trade Simulator Backend (Port 8766 v2.2)...
INFO:websockets.server:server listening on ws://localhost:8766
INFO:root:UI WebSocket server started on ws://localhost:8766
INFO:root:Attempting to connect to OKX L2 feed: wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP
```

> **Important:** Keep this terminal open while using the app to maintain backend operation.

---

### Step 2: Open the HTML Frontend

Open the `trade_frontend.html` file in your web browser by any of these methods:

* Double-click the file
* Right-click the file and select **Open with** and choose your browser
* Drag and drop the file into an open browser window
* Enter the full file path into your browser's address bar (e.g., `file:///path/to/trade_frontend.html`)

---

### Step 3: Use the Application

* **Connection Status:**

  * Orange bar labeled **"Connecting to Backend..."** means it is trying to connect
  * Green bar labeled **"Connected to Backend"** means the connection is established

* **View Live Data:**

  * The **"Processed Output Values"** section updates dynamically with market data
  * The **"Live L2 Order Book"** tables show bid and ask orders in real-time

* **Modify Parameters:**

  * Change input values in the **"Input Parameters"** panel
  * Click the **"Send Parameters to Backend"** button to update calculations on the backend

---

## Debugging Tips

### Check Browser Developer Console

Press **F12** in your browser to open developer tools, then go to the **Console** tab to view WebSocket messages and JavaScript errors.

---

### Common Issues and Solutions

* **Port 8766 Already in Use:**
  Another application is using the port.
  **Fix:** Close the other app or change the port number in both backend and frontend files.

* **Frontend Shows "Disconnected" or Connection Errors:**

  * Confirm backend server is running.
  * Look for errors in the backend terminal.
  * Check VPN status if OKX access is region-restricted.
  * Inspect browser console for WebSocket errors.

* **Backend Running But No Data in UI:**

  * Check for frontend JavaScript errors.
  * Review backend logs for processing issues.
  * Ensure firewall or antivirus is not blocking `localhost` connections.

* **OKX WebSocket Feed Connection Issues:**

  * VPN may be required depending on location.
  * The WebSocket endpoint might be temporarily offline.
  * Verify compliance with OKX API usage policies.

---

## File Overview

* **Backend:** `trade_backend.py`
  Handles WebSocket connections to UI and OKX L2 feed, processes market data.

* **Frontend:** `trade_frontend.html`
  User interface for viewing market data and controlling input parameters.

---

## Connection Details

* **UI WebSocket Server:** `ws://localhost:8766`
* **OKX L2 Order Book Feed:** `wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP`

---

## Support & Contribution

Feel free to:

* Report issues
* Suggest features
* Fork and submit pull requests

---

## License

Add your preferred license information here (e.g., MIT, GPL).

---

*Happy trading! 🚀*

```

---

If you want, I can help generate sample `trade_backend.py` or `trade_frontend.html` templates, or add badges, installation shortcuts, or contribution guidelines. Just let me know!
```

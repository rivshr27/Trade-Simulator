
        // DOM Elements
        const quantityUSDEl = document.getElementById('quantityUSD');
        const volatilityEl = document.getElementById('volatility');
        const feeTierEl = document.getElementById('feeTier');
        const sendParamsBtn = document.getElementById('sendParams');
        const connectionStatusEl = document.getElementById('connectionStatus');

        // Output Elements
        const bestBidEl = document.getElementById('bestBid');
        const bestAskEl = document.getElementById('bestAsk');
        const midPriceEl = document.getElementById('midPrice');
        const expectedSlippageEl = document.getElementById('expectedSlippage');
        const expectedFeesEl = document.getElementById('expectedFees');
        const marketImpactEl = document.getElementById('marketImpact');
        const netCostEl = document.getElementById('netCost');
        const makerTakerEl = document.getElementById('makerTaker');
        const internalLatencyEl = document.getElementById('internalLatency');
        const lastUpdateEl = document.getElementById('lastUpdate');
        const asksTableEl = document.getElementById('asksTable');
        const bidsTableEl = document.getElementById('bidsTable');
        const rawMessageEl = document.getElementById('rawMessage');

        let socket = null;
        const backendUrl = "ws://localhost:8000"; // Port for backend connection
        let reconnectInterval = 5000; // 5 seconds
        let reconnectTimer = null;

        function connectToBackend() {
            // Clear any existing reconnect timer
            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
                reconnectTimer = null;
            }

            if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
                console.info("WebSocket: Already open or connecting.");
                return;
            }

            console.info("WebSocket: Attempting to connect to backend at " + backendUrl);
            connectionStatusEl.textContent = "Connecting to Backend...";
            connectionStatusEl.className = "status-connecting"; // Orange
            
            try {
                socket = new WebSocket(backendUrl);
            } catch (error) {
                console.error("WebSocket: Error creating WebSocket object.", error);
                connectionStatusEl.textContent = "Error creating WebSocket. Check console.";
                connectionStatusEl.className = "status-disconnected"; // Red
                return;
            }

            socket.onopen = function(event) {
                console.log("WebSocket: Connection established with backend.");
                connectionStatusEl.textContent = "Connected to Backend";
                connectionStatusEl.className = "status-connected"; // Green
                // Automatically send current parameters on connect
                sendParameters(); 
            };

            socket.onmessage = function(event) {
                // console.debug("WebSocket: Message received from backend:", event.data);
                rawMessageEl.textContent = "Last message: " + new Date().toLocaleTimeString() + "\n" + JSON.stringify(JSON.parse(event.data), null, 2);
                try {
                    const data = JSON.parse(event.data);
                    updateUI(data);
                } catch (e) {
                    console.error("WebSocket: Error parsing JSON from backend:", e, "\nData:", event.data);
                    rawMessageEl.textContent += "\n\nError parsing message: " + event.data;
                }
            };

            socket.onclose = function(event) {
                console.warn("WebSocket: Connection closed.", "Code:", event.code, "Reason:", event.reason, "wasClean:", event.wasClean);
                let statusMessage = `Disconnected: ${event.reason || 'No reason specified'}.`;
                if (!event.wasClean) { // Attempt to reconnect if not a clean close
                    statusMessage += ' Reconnecting...';
                    reconnectTimer = setTimeout(connectToBackend, reconnectInterval);
                } else {
                    statusMessage += ' Connection closed cleanly.';
                }
                connectionStatusEl.textContent = statusMessage;
                connectionStatusEl.className = "status-disconnected"; // Red
                socket = null; 
            };

            socket.onerror = function(error) {
                console.error("WebSocket: Error occurred:", error);
                // The onclose event will usually be called after an error, triggering reconnect logic if appropriate.
                // No need to directly call connectToBackend here as onclose handles it.
                connectionStatusEl.textContent = "Connection Error. Check console for details.";
                connectionStatusEl.className = "status-disconnected"; // Red
            };
        }

        function sendParameters() {
            if (socket && socket.readyState === WebSocket.OPEN) {
                const quantityUSD = parseFloat(quantityUSDEl.value) || 0;
                const volatility = parseFloat(volatilityEl.value) || 0; // Backend expects 'volatility' for the percentage
                const selectedFeeTierOption = feeTierEl.options[feeTierEl.selectedIndex];
                
                // The backend expects the full fee_tier_data object
                const fee_tier_data = { 
                    maker: parseFloat(selectedFeeTierOption.dataset.maker),
                    taker: parseFloat(selectedFeeTierOption.value) // The value attribute holds the taker rate directly
                };

                const params = {
                    quantityUSD: quantityUSD,
                    volatility: volatility, // Key is 'volatility' for the backend
                    fee_tier_data: fee_tier_data 
                };
                try {
                    socket.send(JSON.stringify(params));
                    console.log("WebSocket: Sent parameters to backend:", params);
                } catch (e) {
                    console.error("WebSocket: Error sending parameters:", e);
                }
            } else {
                console.warn("WebSocket: Not connected. Cannot send parameters.");
                // Optionally alert user or disable button
                // alert("Not connected to backend. Please wait for connection or check console.");
            }
        }

        sendParamsBtn.addEventListener('click', sendParameters);

        function updateUI(data) {
            bestBidEl.textContent = data.bestBid !== undefined ? `$${parseFloat(data.bestBid).toLocaleString(undefined, {minimumFractionDigits:1, maximumFractionDigits: 1})}` : 'N/A';
            bestAskEl.textContent = data.bestAsk !== undefined ? `$${parseFloat(data.bestAsk).toLocaleString(undefined, {minimumFractionDigits:1, maximumFractionDigits: 1})}` : 'N/A';
            midPriceEl.textContent = data.midPrice !== undefined ? `$${parseFloat(data.midPrice).toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits: 2})}` : 'N/A';
            
            expectedSlippageEl.textContent = data.expectedSlippage !== undefined ? `$${parseFloat(data.expectedSlippage).toFixed(2)}` : '0.00';
            expectedFeesEl.textContent = data.expectedFees !== undefined ? `$${parseFloat(data.expectedFees).toFixed(2)}` : '0.00';
            marketImpactEl.textContent = data.marketImpact !== undefined ? `$${parseFloat(data.marketImpact).toFixed(2)}` : '0.00';
            netCostEl.textContent = data.netCost !== undefined ? `$${parseFloat(data.netCost).toFixed(2)}` : '0.00';
            
            makerTakerEl.textContent = data.makerTaker || 'N/A';
            internalLatencyEl.textContent = data.internalLatency !== undefined ? `${parseFloat(data.internalLatency).toFixed(2)} ms` : '0.00 ms';
            lastUpdateEl.textContent = data.lastUpdate || 'N/A';

            updateOrderBookDisplay(data.asks || [], data.bids || []);
        }

        function updateOrderBookDisplay(asks, bids) {
            // Clear previous entries
            asksTableEl.innerHTML = '<tr><th class="text-left">Price</th><th>Quantity</th></tr>'; // Header for asks
            bidsTableEl.innerHTML = '<tr><th class="text-left">Price</th><th>Quantity</th></tr>'; // Header for bids

            (asks || []).slice(0, 5).forEach(ask => { // Ensure asks is an array
                const row = asksTableEl.insertRow();
                row.insertCell().textContent = parseFloat(ask[0]).toLocaleString(undefined, {minimumFractionDigits:1, maximumFractionDigits: 1});
                row.cells[0].classList.add('text-left'); // Align price to the left
                row.insertCell().textContent = ask[1];
            });
            (bids || []).slice(0, 5).forEach(bid => { // Ensure bids is an array
                const row = bidsTableEl.insertRow();
                row.insertCell().textContent = parseFloat(bid[0]).toLocaleString(undefined, {minimumFractionDigits:1, maximumFractionDigits: 1});
                row.cells[0].classList.add('text-left'); // Align price to the left
                row.insertCell().textContent = bid[1];
            });
        }

        // Initial connection attempt when the page loads
        document.addEventListener('DOMContentLoaded', () => {
            console.info("DOM fully loaded. Initializing WebSocket connection.");
            connectToBackend();
        });

   
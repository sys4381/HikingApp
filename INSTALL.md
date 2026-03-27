# 🛠️ Hiking App Installation Guide

Follow these steps to set up the Hiking App on a new machine.

---

### 1. Unzip the Project
Extract the `HikingApp_Backup.zip` file to a folder on your new machine (e.g., `C:\Apps\HikingApp`).

---

### 2. Install Python
Ensure **Python 3.10 or higher** is installed. You can download it from [python.org](https://www.python.org/).

---

### 3. Setup the Backend
Open a terminal (PowerShell or Command Prompt) and navigate to the `backend` folder:

```powershell
cd backend
```

#### Create a Virtual Environment:
```powershell
python -m venv venv
```

#### Activate the Virtual Environment:
- **Windows (PowerShell)**: `.\venv\Scripts\activate`
- **Windows (CMD)**: `venv\Scripts\activate.bat`
- **Mac/Linux**: `source venv/bin/activate`

#### Install Dependencies:
```powershell
pip install -r requirements.txt
```

---

### 4. Run the App

#### Start the Backend:
In the same terminal (with the venv activated), run:
```powershell
python main.py
```
*Note: Keep this terminal open while using the app.*

#### Open the Frontend:
1. Navigate to the `frontend` folder in your file explorer.
2. Double-click **`index.html`** to open it in your web browser.

---

### 5. Ingest Your GPX Files
1. In the app's sidebar, enter the **full path** to your folder containing `.gpx` files.
2. Click **Ingest**.
3. Wait a few moments for the data to process (elevation data is fetched automatically for files that lack it).

---

### Troubleshooting
- **Blank Page**: Ensure you are connected to the internet (required for Leaflet maps and React libraries).
- **CORS Errors**: If you see errors about "Access Control", ensure the backend is running at `http://localhost:8000`.
- **Nominatim 403**: The app uses a custom User-Agent. If you are blocked, ensure your internet connection doesn't have a restrictive firewall.

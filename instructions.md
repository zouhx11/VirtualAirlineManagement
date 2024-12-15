**Instructions for Setting Up a Virtual Environment**

### Linux Instructions

1. **Install `venv` (if not already installed):**
   ```bash
   sudo apt update
   sudo apt install python3-venv
   ```

2. **Navigate to Your Project Directory:**
   ```bash
   cd /path/to/your/project
   ```

3. **Create the Virtual Environment:**
   ```bash
   python3 -m venv venv
   ```

4. **Activate the Virtual Environment:**
   ```bash
   source venv/bin/activate
   ```
   - After activation, you should see `(venv)` at the beginning of your terminal prompt.

5. **Upgrade `pip`:**
   ```bash
   pip install --upgrade pip
   ```

6. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
   ```

7. **Run Your Python Application:**
   ```bash
   python main.py
   ```

8. **Deactivate the Virtual Environment:**
   When you are finished, deactivate the virtual environment:
   ```bash
   deactivate
   ```

---

### Windows Instructions

1. **Ensure Python Is Installed:**
   - Verify Python is installed by running:
     ```cmd
     python --version
     ```
   - If not installed, download and install Python from [python.org](https://www.python.org/).

2. **Navigate to Your Project Directory:**
   ```cmd
   cd \path\to\your\project
   ```

3. **Create the Virtual Environment:**
   ```cmd
   python -m venv venv
   ```

4. **Activate the Virtual Environment:**
   ```cmd
   venv\Scripts\activate
   ```
   - After activation, you should see `(venv)` at the beginning of your terminal prompt.

5. **Upgrade `pip`:**
   ```cmd
   pip install --upgrade pip
   ```

6. **Install Requirements:**
   ```cmd
   pip install -r requirements.txt
   ```

7. **Run Your Python Application:**
   ```cmd
   python main.py
   ```

8. **Deactivate the Virtual Environment:**
   When you are finished, deactivate the virtual environment:
   ```cmd
   deactivate
   ```

---

### Notes
- Ensure `requirements.txt` exists in your project directory and contains all necessary dependencies for your project.
- If you encounter issues with permissions, you can add the `--user` flag to the `pip` commands, but this is rarely needed within a virtual environment.


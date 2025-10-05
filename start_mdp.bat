@echo off
REM Change directory to your project folder if needed
cd /d "C:\path\to\your\project"

REM Activate your virtual environment if you use one
call mdp_env\Scripts\activate

REM Run the Streamlit app
streamlit run main.py

pause
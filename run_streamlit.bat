@echo off
REM Wrapper script to launch the Streamlit app using the correct Python interpreter
REM This avoids needing the "streamlit" command on the PATH.

c:\python314\python.exe -m streamlit run app.py %*

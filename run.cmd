@echo off
setlocal
set "PYTHONPATH=%~dp0src"
python -m faceless_creator %*


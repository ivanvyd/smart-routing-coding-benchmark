@echo off
setlocal
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set CI=1
set NO_COLOR=1
set PAGER=cat
set DATABRICKS_CONFIG_PROFILE=%~1
if "%DATABRICKS_CONFIG_PROFILE%"=="" set DATABRICKS_CONFIG_PROFILE=DEFAULT
pushd "%~dp0"
python -m benchmark.runner.cli run --manifest benchmark\manifest.yaml --profile "%DATABRICKS_CONFIG_PROFILE%" --task easy-001
echo --- exit %errorlevel%
popd
endlocal

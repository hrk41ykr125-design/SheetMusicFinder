@echo off
set REPO_URL=https://github.com/hrk41ykr125-design/SheetMusicFinder.git

echo ========================================
echo  GitHub Auto Push Tool
echo ========================================

rem Check if git is installed
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed. Please install Git for Windows.
    pause
    exit /b
)

rem Check and set git config
echo [INFO] Setting Git user configuration...
git config --global user.email "hrk41ykr125@gmail.com"
git config --global user.name "hrk41ykr125-design"

rem Initialize git if not exists
if not exist ".git" (
    echo [INFO] Initializing git repository...
    git init
)

rem Ensure we are on main branch
git checkout -b main >nul 2>nul
git branch -M main

rem Add remote if not exists
git remote get-url origin >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Setting remote origin...
    git remote add origin %REPO_URL%
) else (
    git remote set-url origin %REPO_URL%
)

echo [INFO] Adding files...
git add .

echo [INFO] Committing changes...
set /p commit_msg="Enter commit message (default: 'initial commit'): "
if "%commit_msg%"=="" set commit_msg=initial commit

rem Try to commit. If it fails, show why.
git commit -m "%commit_msg%"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Commit failed. This usually means:
    echo 1. Your Git Name/Email are not set correctly.
    echo 2. There are no changes to save.
    echo.
    echo Current Git Config:
    git config user.name
    git config user.email
    echo.
    pause
)

rem Ensure the branch is named 'main'
git branch -M main

echo [INFO] Current branch status:
git branch

echo [INFO] Pushing to GitHub...
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Push failed. 
    echo If this is the first time, check if you have created the repository on GitHub.
    echo Also, make sure you are logged in to GitHub.
) else (
    echo.
    echo [SUCCESS] Changes pushed successfully!
)

pause

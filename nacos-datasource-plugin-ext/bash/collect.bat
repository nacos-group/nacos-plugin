@echo off
echo collect begin ...

set src_path=..
set dst_path=.\deploy
set target_dir=target

:: 脚本功能
:: 将打包的结果收集到 deploy 目录中，并将原来的 deploy 目录移动到 backup 目录
:: 也就是说，deploy 是最新的打包结果，backup 是上一次打包结果

mkdir %dst_path%
mkdir .\backup

rd /q /s .\backup
move /Y %dst_path% .\backup

rd /q /s %dst_path%
mkdir %dst_path%

rd %src_path%\%target_dir%
for /F %%i in ('dir /S /B %src_path%\%target_dir%') do (

      for /F %%j in ('dir  /B %%i\*.jar') do (
          echo copy /B /Y %%i\%%j %dst_path%\
          copy /B /Y %%i\%%j %dst_path%\
      )
      for /F %%j in ('dir  /B %%i\*.war') do (
          echo copy /B /Y %%i\%%j %dst_path%\
          copy /B /Y %%i\%%j %dst_path%\
      )
      for /F %%j in ('dir  /B %%i\*.tar') do (
          echo copy /B /Y %%i\%%j %dst_path%\
          copy /B /Y %%i\%%j %dst_path%\
      )
      for /F %%j in ('dir  /B %%i\*.gz') do (
          echo copy /B /Y %%i\%%j %dst_path%\
          copy /B /Y %%i\%%j %dst_path%\
      )
)


echo collect done.

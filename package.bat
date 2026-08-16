title 正在打包中，请稍后...
pyinstaller --windowed --onefile --clean --noconfirm --icon=icon.ico --name="锄大地" --add-data "icon.ico;." 锄大地.pyw
@echo off
cls
title ^^_^^
echo 打包完毕！请按任意键退出...
pause>nul

::注意，如果打包过程中发生错误，本程序概不显示！
::此外，--add-data参数需置于最后
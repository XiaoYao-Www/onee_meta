# 編譯命令
```
nuitka app.py --standalone --windows-icon-from-ico=assets/icon.png --include-data-dir=assets=assets --enable-plugin=pyside6 -j 20 --output-dir=build
```

# 生成翻譯檔
```
pyside6-lupdate lupdate_stub_help.py -ts zh_TW.ts -locations none
```
```
pyside6-lrelease zh_TW.ts
```
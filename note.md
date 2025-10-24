# 編譯命令
```
nuitka app.py ^
  --standalone ^
  --show-progress ^
  --disable-console ^
  --remove-output ^
  --noinclude-default-mode=nofollow ^
  --windows-icon-from-ico=assets/icon.png ^
  --include-data-dir=assets=assets ^
  --enable-plugin=pyside6 ^
  --include-qt-plugins=sensible ^
  --lto=yes ^
  -j 20 ^
  --output-dir=dev/build
```

# 生成翻譯檔
```
pyside6-lupdate lupdate_stub_help.py -ts zh_TW.ts -locations none
```
```
pyside6-lrelease zh_TW.ts
```
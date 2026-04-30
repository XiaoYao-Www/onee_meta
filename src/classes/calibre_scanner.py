import subprocess
import shutil
import os
import json
from typing import cast, List, Dict, Any
import re
import xml.etree.ElementTree as ET

class CalibreSidecar:
    def __init__(self, custom_path=None):
        self.exe_path = self._find_calibre_exe(custom_path)
        if not self.exe_path:
            raise RuntimeError("找不到 Calibre 安裝路徑，請手動指定。")
        
        self.env = os.environ.copy()
        # 加強強制英文 + Calibre 語言覆蓋
        self.env["LANG"] = "en_US.UTF-8"
        self.env["LC_ALL"] = "en_US.UTF-8"
        self.env["LANGUAGE"] = "en"
        self.env["CALIBRE_OVERRIDE_LANG"] = "en"
        
        self._setup_portable_config(custom_path)
        
        # 記錄 calibre-debug 的完整路徑（跟 calibre-customize 同目錄）
        calibre_dir = os.path.dirname(self.exe_path)
        self.debug_exe = os.path.join(calibre_dir, "calibre-debug.exe" if os.name == "nt" else "calibre-debug")

    def _find_calibre_exe(self, custom_path):
        if custom_path:
            exe = os.path.join(custom_path, "calibre-customize.exe" if os.name == "nt" else "calibre-customize")
            if os.path.exists(exe):
                return exe
        return shutil.which("calibre-customize")

    def _setup_portable_config(self, custom_path):
        if custom_path:
            parent_dir = os.path.dirname(os.path.abspath(custom_path))
            portable_settings = os.path.join(parent_dir, "Calibre Settings")
            if os.path.exists(portable_settings):
                self.env["CALIBRE_CONFIG_DIRECTORY"] = portable_settings
                print(f"檢測到便攜版設定目錄: {portable_settings}")

    def list_metadata_plugins(self) -> List[Dict[str, Any]]:
        """最穩定方式：透過 calibre-debug 呼叫官方 API 取得所有 Metadata 來源插件"""
        try:
            # 建立臨時 Python 腳本來執行 Calibre 內部 API
            script_content = '''
import json
from calibre.customize.ui import metadata_plugins

# 取得所有 identify（元數據抓取）類型的插件
plugins = list(metadata_plugins(['identify']))

result = []
for p in plugins:
    result.append({
        "name": getattr(p, "name", "Unknown"),
        "version": getattr(p, "version", "N/A"),
        "description": getattr(p, "description", ""),
        "author": getattr(p, "author", ""),
        "type": getattr(p, "type", "Metadata source")
    })

print(json.dumps(result, ensure_ascii=False, indent=2))
'''

            # 寫入臨時腳本
            temp_script = os.path.join(os.path.expanduser("~"), "calibre_temp_list_plugins.py")
            with open(temp_script, "w", encoding="utf-8") as f:
                f.write(script_content)

            # 執行 calibre-debug -e
            cmd = [cast(str, self.debug_exe), "-e", temp_script]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=self.env,
                check=False  # 不強制 check=True，避免小錯誤中斷
            )

            # 清理臨時檔案
            if os.path.exists(temp_script):
                os.remove(temp_script)

            if result.returncode != 0:
                print(f"calibre-debug 執行錯誤: {result.stderr}")
                return self._fallback_list()  # 如果失敗，退回備用方法

            # 解析 JSON 輸出
            try:
                plugins_list = json.loads(result.stdout)
                print(f"成功取得 {len(plugins_list)} 個 Metadata 來源插件")
                return plugins_list
            except json.JSONDecodeError:
                print("JSON 解析失敗，原始輸出：")
                print(result.stdout)
                return []

        except Exception as e:
            print(f"取得 Metadata 插件時發生錯誤: {e}")
            return self._fallback_list()

    def _fallback_list(self):
        """備用方法：使用 calibre-customize --list-plugins"""
        print("使用備用方法 (calibre-customize --list-plugins)")
        try:
            result = subprocess.run(
                [cast(str, self.exe_path), "--list-plugins"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=self.env,
                check=True
            )
            # 簡單解析（不完美，但至少有東西）
            plugins = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if line and not line.startswith(("[", "Available", "=")) and "(" in line:
                    match = re.search(r"^(.*?)\s*\(([\d\.,]+)\)", line)
                    if match:
                        plugins.append({
                            "name": match.group(1).strip(),
                            "version": match.group(2).strip(),
                            "description": ""
                        })
            return plugins
        except Exception:
            return []
        
    def parse_calibre_stdout(self, stdout: str):
        entries = []
    
        VALID_KEYS = {
            "Title",
            "Author(s)",
            "Publisher",
            "Tags",
            "Languages",
            "Rating",
            "Identifiers"
        }
        
        blocks = re.split(r"\n---+\n", stdout)
        
        for block in blocks:
            if "Title" not in block:
                continue
            
            entry = {}
            
            for line in block.splitlines():
                if ":" not in line:
                    continue
                
                key, value = line.split(":", 1)
                key = key.strip()
                
                # 👉 關鍵：只保留合法欄位
                if key not in VALID_KEYS:
                    continue
                
                entry[key] = value.strip()
            
            entries.append(entry)
    
        return entries  
    
    def extract_plugin_block(self, stdout: str, plugin_name="E-hentai Galleries"):
        lines = stdout.splitlines()
        
        inside = False
        buffer = []

        for line in lines:
            # 進入 plugin 區塊
            if plugin_name in line and "****" in line:
                inside = True
                continue
            
            # 離開 plugin 區塊（遇到下一個 **** header）
            if inside and "****" in line:
                break
            
            if inside:
                buffer.append(line)
        
        return "\n".join(buffer)
    
    def fetch_metadata(self, title=None, authors=None, isbn=None, 
                       allowed_plugins=None, 
                       timeout=30, 
                       output_opf=None) -> list | None:
        
        if not any([title, authors, isbn]):
            raise ValueError("必須提供 title、authors 或 isbn 其中一項")
        
        cmd = [os.path.join(os.path.dirname(cast(str, self.exe_path)), 
               "fetch-ebook-metadata.exe" if os.name == "nt" else "fetch-ebook-metadata")]

        if title: cmd.extend(["--title", title])
        if authors: cmd.extend(["--authors", authors])
        if isbn: cmd.extend(["--isbn", isbn])
        if allowed_plugins:
            for p in allowed_plugins:
                cmd.extend(["--allowed-plugin", p])

        cmd.extend(["--timeout", str(timeout)])

        cmd.append("-v")  # 开启调试输出

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=self.env,
                timeout=timeout + 10
            )

            plugin_text = self.extract_plugin_block(result.stdout + "\n" + result.stderr)
            entries = self.parse_calibre_stdout(plugin_text)

            return entries

        except Exception as e:
            print(f"執行 fetch-ebook-metadata 時發生錯誤: {e}")
            return None

# ====================== 使用範例 ======================
if __name__ == "__main__":
    path = r"C:\no_installation_required\Calibre Portable\Calibre"
    scanner = CalibreSidecar(custom_path=path)

    print("開始聚合抓取元數據（會同時查詢多個來源）...")

    # print(scanner.list_metadata_plugins())

    # 方法一：使用全部已安裝的插件進行聚合搜索
    opf_content = scanner.fetch_metadata(
        title="Author(s)'",
    )

    if opf_content:
        print("抓取成功！部分 OPF 內容：")
        print(opf_content)   # 只顯示前面部分
Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
objShell.Run "pythonw main_orchestrator.py", 0, False
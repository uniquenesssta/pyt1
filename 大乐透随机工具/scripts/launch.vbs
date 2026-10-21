Option Explicit
Dim fs, shell, scriptPath, command
Set fs = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
scriptPath = fs.BuildPath(fs.GetParentFolderName(WScript.ScriptFullName), "start.ps1")
command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File " & Chr(34) & scriptPath & Chr(34)
shell.Run command, 0, False

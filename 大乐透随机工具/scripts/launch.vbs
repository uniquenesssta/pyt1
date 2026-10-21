Option Explicit
Dim fs, shell, scriptPath, command, toolRoot, cachePath, handle, pythonWindow, cachedRoot
Set fs = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
toolRoot = fs.GetParentFolderName(fs.GetParentFolderName(WScript.ScriptFullName))
cachePath = fs.BuildPath(toolRoot, "user_data\launcher-v1.txt")
pythonWindow = ""
cachedRoot = ""
If fs.FileExists(cachePath) Then
    On Error Resume Next
    Set handle = fs.OpenTextFile(cachePath, 1, False, -1)
    pythonWindow = handle.ReadLine
    cachedRoot = handle.ReadLine
    handle.Close
    On Error GoTo 0
End If
If cachedRoot = toolRoot And fs.FileExists(pythonWindow) Then
    shell.CurrentDirectory = toolRoot
    command = Chr(34) & pythonWindow & Chr(34) & " " & Chr(34) & fs.BuildPath(toolRoot, "main.py") & Chr(34)
    shell.Run command, 0, False
Else
    scriptPath = fs.BuildPath(fs.GetParentFolderName(WScript.ScriptFullName), "start.ps1")
    command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File " & Chr(34) & scriptPath & Chr(34)
    shell.Run command, 0, False
End If

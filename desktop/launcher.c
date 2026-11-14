/* Minimal Windows launcher. Starts only the bundled, adjacent Python runtime. */
#ifndef UNICODE
#define UNICODE
#endif
#define _UNICODE
#include <windows.h>
#include <wchar.h>
#include <stdio.h>

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR args, int show) {
    (void)instance; (void)previous; (void)args; (void)show;
    wchar_t root[32768], executable[32768], command[65536];
    DWORD length = GetModuleFileNameW(NULL, root, 32768);
    if (!length || length >= 32768) return 1;
    wchar_t *end = wcsrchr(root, L'\\');
    if (!end) return 1;
    *end = L'\0';
    int n = _snwprintf(executable, 32768, L"%ls\\runtime\\pythonw.exe", root);
    if (n < 0 || n >= 32768) return 1;
    n = _snwprintf(command, 65536, L"\"%ls\" \"%ls\\desktop\\main.py\"", executable, root);
    if (n < 0 || n >= 65536) return 1;
    STARTUPINFOW startup = {0};
    PROCESS_INFORMATION process = {0};
    startup.cb = sizeof(startup);
    if (!CreateProcessW(executable, command, NULL, NULL, FALSE, CREATE_NO_WINDOW,
                        NULL, root, &startup, &process)) {
        MessageBoxW(NULL,
            L"Не вдалося запустити Fleng. Розпакуй увесь ZIP у папку, а потім відкрий Fleng.exe.",
            L"Fleng", MB_OK | MB_ICONERROR);
        return 1;
    }
    CloseHandle(process.hThread);
    WaitForSingleObject(process.hProcess, INFINITE);
    DWORD code = 1;
    GetExitCodeProcess(process.hProcess, &code);
    CloseHandle(process.hProcess);
    return (int)code;
}
